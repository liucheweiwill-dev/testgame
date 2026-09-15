from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

import pytest
from tools import mutation_gate

# The tree this suite is running in. Under mutmut that is the mutants/ copy, and
# it must stay so: tools/ is in source_paths, so the gate under test is the
# mutated one. Resolving out of the copy here would test the original file and
# kill no mutant.
RUN_ROOT = Path(__file__).resolve().parents[1]


def _repository_root() -> Path:
    # mutmut copies only the source it mutates, so PROJECT.md, the workflow and
    # pyproject.toml do not exist under mutants/. The gauntlet-scope scenarios
    # are about the repository's own files and must read them where they are.
    test_path = Path(__file__).resolve()
    for parent in test_path.parents:
        if parent.name == "mutants":
            return parent.parent
    return test_path.parents[1]


REPOSITORY_ROOT = _repository_root()


def _repository_text(relative: str) -> str:
    path = REPOSITORY_ROOT / relative
    assert path.is_file(), (
        f"Repository root resolution failed: resolved {REPOSITORY_ROOT}; "
        f"expected {path} to be an existing file"
    )
    return path.read_text(encoding="utf-8")


RUN_OUTPUT = (
    "\r⠋ 129/129  🎉 129 🫥 0  ⏰ 0  🤔 0  🙁 0  🔇 0  🧙 0\n10.09 mutations/second\n"
)
ZERO_MUTANTS_RUN_OUTPUT = (
    "\r⠋ 0/0  🎉 0 🫥 0  ⏰ 0  🤔 0  🙁 0  🔇 0  🧙 0\n0.00 mutations/second\n"
)
MUTANT = "domain.x.y__mutmut_1"


def _result_line(status: str, mutant: str = MUTANT) -> str:
    return f"    {mutant}: {status}\n"


def _completed(
    *, returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


class StubRunner:
    def __init__(self, *responses: subprocess.CompletedProcess[str]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(tuple(command))
        if not self.responses:
            raise AssertionError(f"Unexpected producer command: {command!r}")
        return self.responses.pop(0)


def _run_gate(
    results: str,
    *later_responses: subprocess.CompletedProcess[str],
    run_output: str = RUN_OUTPUT,
) -> tuple[int, str, StubRunner]:
    runner = StubRunner(
        _completed(stdout=run_output),
        _completed(stdout=results),
        *later_responses,
    )
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert not runner.responses
    return exit_code, output.getvalue(), runner


def _assert_status_fails(status: str) -> None:
    line = _result_line(status)

    exit_code, output, runner = _run_gate(line)

    assert exit_code == 1
    assert line.rstrip() in output
    assert len(runner.calls) == 2


def _retry_run_output(initial: float = 15.0, retried: float = 30.0) -> str:
    return (
        f"mutation-gate retry budget: timeout_multiplier={initial:g} -> {retried:g}\n"
    )


# Status-vocabulary scenarios.
def test_survived_fails() -> None:
    _assert_status_fails("survived")


def test_no_tests_fails_with_exact_two_word_status() -> None:
    _assert_status_fails("no tests")


def test_not_checked_fails_with_exact_two_word_status() -> None:
    _assert_status_fails("not checked")


def test_skipped_fails() -> None:
    _assert_status_fails("skipped")


def test_suspicious_fails() -> None:
    _assert_status_fails("suspicious")


def test_caught_by_type_check_fails() -> None:
    _assert_status_fails("caught by type check")


def test_segfault_fails() -> None:
    _assert_status_fails("segfault")


def test_check_was_interrupted_by_user_fails() -> None:
    _assert_status_fails("check was interrupted by user")


def test_timeout_retries_with_a_larger_budget_and_classifies_retry_status() -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=_result_line("survived")),
    )

    assert exit_code == 1
    assert "timeout" in output
    assert "retry outcome: survived" in output
    assert "timeout_multiplier=15 -> 30" in output
    assert len(runner.calls) == 4
    assert runner.calls[2][0] == sys.executable
    assert MUTANT in runner.calls[2]


def test_unrecognised_status_fails_and_names_it() -> None:
    exit_code, output, _ = _run_gate(_result_line("banana"))

    assert exit_code == 1
    assert "unrecognised status 'banana'" in output


def test_duplicate_mutant_fails_and_names_it() -> None:
    line = _result_line("survived")

    exit_code, output, _ = _run_gate(line + line)

    assert exit_code == 1
    assert f"duplicate mutmut results line for mutant '{MUTANT}'" in output


# Parsing scenarios.
def test_four_space_result_line_is_parsed() -> None:
    assert mutation_gate.parse_results("    domain.x.y__mutmut_1: survived") == [
        ("domain.x.y__mutmut_1", "survived")
    ]


def test_nonblank_line_without_separator_fails_and_names_line() -> None:
    malformed = "    domain.x.y__mutmut_1 survived"

    exit_code, output, _ = _run_gate(malformed)

    assert exit_code == 1
    assert "malformed mutmut results line" in output
    assert repr(malformed) in output


def test_unexpected_header_fails_as_malformed() -> None:
    header = "Mutant results"

    exit_code, output, _ = _run_gate(header)

    assert exit_code == 1
    assert "malformed mutmut results line" in output
    assert repr(header) in output


def test_blank_line_is_ignored() -> None:
    assert mutation_gate.parse_results("\n   \n\t\n") == []


# Exit-behaviour scenarios.
def test_no_non_killed_results_with_generated_mutants_passes_and_prints_count() -> None:
    exit_code, output, _ = _run_gate("")

    assert exit_code == 0
    assert "129 mutants generated" in output


def test_only_timeouts_resolved_as_killed_pass_and_print_retry_outcome() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=""),
    )

    assert exit_code == 0
    assert f"{MUTANT}: timeout" in output
    assert "retry outcome: killed" in output
    assert "timeout_multiplier=15 -> 30" in output


def test_timeout_again_on_larger_budget_counts_as_killed() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=_result_line("timeout")),
    )

    assert exit_code == 0
    assert "retry outcome: timeout (counted as killed)" in output


def test_one_survivor_exits_one_and_prints_line() -> None:
    line = _result_line("survived")

    exit_code, output, _ = _run_gate(line)

    assert exit_code == 1
    assert line.rstrip() in output


def test_timeout_beside_survivor_exits_one_and_reports_both() -> None:
    timeout_line = _result_line("timeout")
    survived_line = _result_line("survived", "domain.x.z__mutmut_2")

    exit_code, output, _ = _run_gate(
        timeout_line + survived_line,
        _completed(stdout=_retry_run_output()),
        _completed(stdout=survived_line),
    )

    assert exit_code == 1
    assert f"{MUTANT}: timeout" in output
    assert "retry outcome: killed" in output
    assert survived_line.rstrip() in output


@pytest.mark.parametrize("failed_producer", ["run", "results"])
def test_nonzero_producer_exit_propagates_as_gate_failure(
    failed_producer: str,
) -> None:
    failure = _completed(returncode=7, stderr="producer exploded\n")
    responses = (
        (failure,)
        if failed_producer == "run"
        else (_completed(stdout=RUN_OUTPUT), failure)
    )
    runner = StubRunner(*responses)
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert f"mutmut {failed_producer} failed with exit code 7" in output.getvalue()
    assert "producer exploded" in output.getvalue()
    assert not runner.responses


def test_empty_results_and_zero_generated_mutants_fails() -> None:
    exit_code, output, _ = _run_gate("", run_output=ZERO_MUTANTS_RUN_OUTPUT)

    assert exit_code == 1
    assert "no mutants were generated" in output


def test_configured_mutmut_command_prefixes_each_producer_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MUTATION_GATE_MUTMUT_COMMAND",
        json.dumps(["custom-mutmut", "--isolated"]),
    )

    exit_code, output, runner = _run_gate("")

    assert exit_code == 0
    assert "mutation gate passed" in output
    assert runner.calls == [
        ("custom-mutmut", "--isolated", "run"),
        ("custom-mutmut", "--isolated", "results"),
    ]


@pytest.mark.parametrize(
    "raw_command, expected_message",
    [
        pytest.param(
            "not JSON",
            "must be a JSON array of strings",
            id="invalid-json",
        ),
        pytest.param(
            json.dumps("mutmut"),
            "must be a non-empty JSON array of non-empty strings",
            id="not-an-array",
        ),
        pytest.param(
            json.dumps([]),
            "must be a non-empty JSON array of non-empty strings",
            id="empty-array",
        ),
        pytest.param(
            json.dumps([1]),
            "must be a non-empty JSON array of non-empty strings",
            id="non-string-part",
        ),
        pytest.param(
            json.dumps([""]),
            "must be a non-empty JSON array of non-empty strings",
            id="empty-string-part",
        ),
    ],
)
def test_invalid_configured_mutmut_command_fails_before_starting_producer(
    monkeypatch: pytest.MonkeyPatch,
    raw_command: str,
    expected_message: str,
) -> None:
    monkeypatch.setenv("MUTATION_GATE_MUTMUT_COMMAND", raw_command)
    runner = StubRunner()
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert expected_message in output.getvalue()
    assert runner.calls == []


def test_producer_start_oserror_fails_and_names_stage() -> None:
    def unavailable_runner(
        command: Sequence[str],
    ) -> subprocess.CompletedProcess[str]:
        raise OSError(f"cannot execute {command[0]}")

    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=unavailable_runner, output=output)

    assert exit_code == 1
    assert "mutmut run failed to start: cannot execute mutmut" in output.getvalue()


def test_failed_producer_prints_stdout_and_stderr_as_separate_lines() -> None:
    runner = StubRunner(
        _completed(returncode=7, stdout="partial stdout", stderr="partial stderr")
    )
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert output.getvalue().splitlines() == [
        "mutmut run failed with exit code 7",
        "partial stdout",
        "partial stderr",
    ]


def test_failed_producer_preserves_terminated_stdout_without_blank_line() -> None:
    runner = StubRunner(_completed(returncode=7, stdout="producer output\n"))
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert output.getvalue() == (
        "mutmut run failed with exit code 7\nproducer output\n"
    )


def test_missing_generated_mutant_count_fails_closed() -> None:
    exit_code, output, _ = _run_gate("", run_output="run completed without summary\n")

    assert exit_code == 1
    assert "could not read the generated-mutant count from mutmut run" in output


@pytest.mark.parametrize(
    "retry_output",
    [
        pytest.param("retry completed without a budget report\n", id="missing"),
        pytest.param(
            _retry_run_output() + _retry_run_output(30.0, 60.0),
            id="duplicate",
        ),
    ],
)
def test_retry_fails_when_it_does_not_report_exactly_one_raised_budget(
    retry_output: str,
) -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=retry_output),
    )

    assert exit_code == 1
    assert f"{MUTANT}: timeout; retry budget invalid" in output
    assert "timeout retry did not report exactly one raised budget" in output
    assert len(runner.calls) == 3


def test_retry_fails_when_reported_budget_was_not_raised() -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output(15.0, 15.0)),
    )

    assert exit_code == 1
    assert f"{MUTANT}: timeout; retry budget invalid" in output
    assert "timeout retry budget was not raised: timeout_multiplier=15 -> 15" in output
    assert len(runner.calls) == 3


def test_retry_producer_failure_exits_one_and_names_stage() -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(returncode=7, stderr="retry producer exploded\n"),
    )

    assert exit_code == 1
    assert "mutmut retry for" in output
    assert "failed with exit code 7" in output
    assert f"{MUTANT}: timeout; retry producer failed" in output
    assert "retry producer exploded" in output
    assert len(runner.calls) == 3


def test_retry_result_producer_failure_exits_one_and_names_stage() -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(returncode=8, stderr="retry results exploded\n"),
    )

    assert exit_code == 1
    assert "mutmut results after retry failed with exit code 8" in output
    assert f"{MUTANT}: timeout; retry result producer failed" in output
    assert "timeout_multiplier=15 -> 30" in output
    assert "retry results exploded" in output
    assert len(runner.calls) == 4


def test_malformed_retry_result_exits_one_and_names_stage() -> None:
    malformed = "retry results are malformed"
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=malformed),
    )

    assert exit_code == 1
    assert f"{MUTANT}: timeout; retry result malformed" in output
    assert "timeout_multiplier=15 -> 30" in output
    assert "mutation gate failed: malformed mutmut results line" in output
    assert repr(malformed) in output
    assert len(runner.calls) == 4


def test_main_uses_real_runner_with_utf8_subprocess_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("MUTATION_GATE_MUTMUT_COMMAND", raising=False)
    responses = [
        _completed(stdout=RUN_OUTPUT),
        _completed(stdout=""),
    ]
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def stub_subprocess_run(
        command: Sequence[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append((tuple(command), kwargs))
        return responses.pop(0)

    monkeypatch.setattr(mutation_gate.subprocess, "run", stub_subprocess_run)

    exit_code = mutation_gate.main()

    assert exit_code == 0
    assert capsys.readouterr().out == "mutation gate passed: 129 mutants generated\n"
    assert [command for command, _ in calls] == [
        ("mutmut", "run"),
        ("mutmut", "results"),
    ]
    assert responses == []
    for _, kwargs in calls:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert environment["PYTHONIOENCODING"] == "utf-8"
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["check"] is False


def test_script_guard_turns_configuration_failure_into_process_exit_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MUTATION_GATE_MUTMUT_COMMAND", "not JSON")

    with pytest.raises(SystemExit) as raised:
        runpy.run_path(
            str(RUN_ROOT / "tools/mutation_gate.py"),
            run_name="__main__",
        )

    assert raised.value.code == 1
    assert (
        "MUTATION_GATE_MUTMUT_COMMAND must be a JSON array" in capsys.readouterr().out
    )


# The gate's own gauntlet-scope scenarios.
def _project_and_workflow_text() -> tuple[str, str]:
    return (
        _repository_text("PROJECT.md"),
        _repository_text(".github/workflows/gauntlet.yml"),
    )


def test_types_command_includes_tools_in_project_and_workflow() -> None:
    project, workflow = _project_and_workflow_text()
    command = "uv run mypy src tools"

    assert command in project
    assert command in workflow


def test_cleanup_command_includes_tools_in_project_and_workflow() -> None:
    project, workflow = _project_and_workflow_text()
    command = "uv run vulture src tests tools"

    assert command in project
    assert command in workflow


def test_changed_line_coverage_includes_tools_in_project_and_workflow() -> None:
    project, workflow = _project_and_workflow_text()
    command = "uv run pytest --cov=src --cov=tools --cov-branch --cov-report=xml"

    assert command in project
    assert command in workflow


def test_mutation_source_paths_include_domain_and_tools() -> None:
    config = tomllib.loads(_repository_text("pyproject.toml"))

    assert config["tool"]["mutmut"]["source_paths"] == ["src/domain", "tools"]


def test_gate_test_runs_in_normal_test_suite() -> None:
    config = tomllib.loads(_repository_text("pyproject.toml"))

    assert config["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert Path(__file__).parent.name == "tests"


# Deprecation-removal scenarios.
def test_mutmut_configuration_uses_source_paths_not_paths_to_mutate() -> None:
    config = tomllib.loads(_repository_text("pyproject.toml"))["tool"]["mutmut"]

    assert "paths_to_mutate" not in config
    assert config["source_paths"] == ["src/domain", "tools"]


def test_mutation_step_invokes_gate_in_project_and_workflow() -> None:
    project, workflow = _project_and_workflow_text()
    command = "uv run python tools/mutation_gate.py"

    assert command in project
    assert command in workflow


def test_vulture_configuration_includes_tools() -> None:
    config = tomllib.loads(_repository_text("pyproject.toml"))

    assert config["tool"]["vulture"]["paths"] == ["src", "tests", "tools"]


def test_subprocess_gate_rejects_stubbed_survivor(tmp_path: Path) -> None:
    producer = tmp_path / "stub_mutmut.py"
    producer.write_text(
        """\
import sys

if sys.argv[1:] == ["run"]:
    print("\\r⠋ 1/1  🎉 0 🫥 0  ⏰ 0  🤔 0  🙁 1  🔇 0  🧙 0")
    raise SystemExit(0)
if sys.argv[1:] == ["results"]:
    print("    domain.x.y__mutmut_1: survived")
    raise SystemExit(0)
raise SystemExit(9)
""",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["MUTATION_GATE_MUTMUT_COMMAND"] = json.dumps(
        [sys.executable, str(producer)]
    )

    completed = subprocess.run(
        [sys.executable, str(RUN_ROOT / "tools/mutation_gate.py")],
        cwd=RUN_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "domain.x.y__mutmut_1: survived" in completed.stdout


# Mutation-survivor scenarios. The first CI run that mutated tools/ left 34
# survivors in this module: the scenarios above reach every branch, but assert
# with substring checks, so a mutated message still contains what they look for.
# These pin exact values instead.
def _assert_malformed(line: str) -> None:
    with pytest.raises(mutation_gate.GateError) as raised:
        mutation_gate.parse_results(line)

    assert str(raised.value) == f"malformed mutmut results line: {line!r}"


def test_three_space_result_line_is_malformed() -> None:
    _assert_malformed("   domain.x.y__mutmut_1: survived")


def test_five_space_result_line_is_malformed() -> None:
    _assert_malformed("     domain.x.y__mutmut_1: survived")


def test_empty_mutant_name_is_malformed() -> None:
    _assert_malformed("    : survived")


def test_empty_status_is_malformed() -> None:
    _assert_malformed("    domain.x.y__mutmut_1: ")


def test_status_with_trailing_space_is_malformed() -> None:
    _assert_malformed("    domain.x.y__mutmut_1: survived ")


def test_blank_line_between_results_does_not_stop_parsing() -> None:
    parsed = mutation_gate.parse_results(
        "    domain.x.y__mutmut_1: survived\n\n    domain.x.y__mutmut_2: skipped\n"
    )

    assert parsed == [
        ("domain.x.y__mutmut_1", "survived"),
        ("domain.x.y__mutmut_2", "skipped"),
    ]


def test_results_keep_input_order_and_every_character_after_the_indent() -> None:
    parsed = mutation_gate.parse_results("    b.m__mutmut_2: timeout\n    a: skipped\n")

    assert parsed == [("b.m__mutmut_2", "timeout"), ("a", "skipped")]


def test_generated_mutant_count_reads_the_last_summary_total() -> None:
    run_output = "\r⠋ 3/7  🎉 3 🫥 0\n\r⠋ 11/23  🎉 11 🫥 0\n"

    assert mutation_gate._generated_mutant_count(run_output) == 23


def test_default_mutmut_command_is_exactly_mutmut(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MUTATION_GATE_MUTMUT_COMMAND", raising=False)

    assert mutation_gate._configured_mutmut_command() == ("mutmut",)


def test_retry_command_runs_the_retry_program_with_the_factor_and_mutant() -> None:
    assert mutation_gate._retry_command(MUTANT) == (
        sys.executable,
        "-c",
        mutation_gate._RETRY_PROGRAM,
        "2.0",
        MUTANT,
    )


def test_retry_budget_returns_the_exact_rendered_transition() -> None:
    reported = mutation_gate._retry_budget(_retry_run_output())

    assert reported == "timeout_multiplier=15 -> 30"


def test_two_reported_retry_budgets_fail() -> None:
    with pytest.raises(mutation_gate.GateError) as raised:
        mutation_gate._retry_budget(_retry_run_output() + _retry_run_output())

    assert str(raised.value) == (
        "timeout retry did not report exactly one raised budget"
    )


def test_print_messages_terminates_only_unterminated_messages() -> None:
    output = StringIO()

    mutation_gate._print_messages(["first", "second\n"], output)

    assert output.getvalue() == "first\nsecond\n"


def test_print_messages_writes_nothing_when_there_are_no_messages() -> None:
    output = StringIO()

    mutation_gate._print_messages([], output)

    assert output.getvalue() == ""


def test_failed_producer_terminates_unterminated_stderr() -> None:
    runner = StubRunner(_completed(returncode=3, stderr="stderr tail"))
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert output.getvalue() == "mutmut run failed with exit code 3\nstderr tail\n"


def test_failed_producer_preserves_terminated_stderr() -> None:
    runner = StubRunner(_completed(returncode=3, stderr="stderr tail\n"))
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert output.getvalue() == "mutmut run failed with exit code 3\nstderr tail\n"


def test_results_producer_failure_names_the_results_stage() -> None:
    runner = StubRunner(_completed(stdout=RUN_OUTPUT), _completed(returncode=5))
    output = StringIO()

    exit_code = mutation_gate.run_gate(runner=runner, output=output)

    assert exit_code == 1
    assert output.getvalue() == "mutmut results failed with exit code 5\n"


def test_passing_gate_prints_only_the_exact_summary_line() -> None:
    exit_code, output, runner = _run_gate("")

    assert exit_code == 0
    assert output == "mutation gate passed: 129 mutants generated\n"
    assert runner.calls == [("mutmut", "run"), ("mutmut", "results")]


def test_zero_generated_mutants_prints_only_the_exact_failure_line() -> None:
    exit_code, output, _ = _run_gate("", run_output=ZERO_MUTANTS_RUN_OUTPUT)

    assert exit_code == 1
    assert output == "mutation gate failed: no mutants were generated\n"


def test_retry_note_for_a_killed_retry_is_exact() -> None:
    exit_code, output, runner = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=""),
    )

    assert exit_code == 0
    assert output == (
        f"    {MUTANT}: timeout; retry outcome: killed; "
        "timeout_multiplier=15 -> 30\n"
        "mutation gate passed: 129 mutants generated\n"
    )
    assert runner.calls == [
        ("mutmut", "run"),
        ("mutmut", "results"),
        mutation_gate._retry_command(MUTANT),
        ("mutmut", "results"),
    ]


def test_retry_note_for_a_second_timeout_is_exact() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=_result_line("timeout")),
    )

    assert exit_code == 0
    assert output == (
        f"    {MUTANT}: timeout; retry outcome: timeout (counted as killed); "
        "timeout_multiplier=15 -> 30\n"
        "mutation gate passed: 129 mutants generated\n"
    )


def test_retry_resolving_to_survived_fails_and_lists_the_mutant_twice() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=_result_line("survived")),
    )

    assert exit_code == 1
    assert output == (
        f"    {MUTANT}: timeout; retry outcome: survived; "
        "timeout_multiplier=15 -> 30\n"
        f"    {MUTANT}: survived\n"
    )


def test_mutant_absent_from_retry_results_counts_as_killed() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("timeout"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=_result_line("survived", mutant="other.m__mutmut_9")),
    )

    assert exit_code == 0
    assert output == (
        f"    {MUTANT}: timeout; retry outcome: killed; "
        "timeout_multiplier=15 -> 30\n"
        "mutation gate passed: 129 mutants generated\n"
    )


def test_retry_notes_are_printed_before_failures() -> None:
    exit_code, output, _ = _run_gate(
        _result_line("survived", mutant="a__mutmut_1")
        + _result_line("timeout", mutant="b__mutmut_2"),
        _completed(stdout=_retry_run_output()),
        _completed(stdout=""),
    )

    assert exit_code == 1
    assert output == (
        "    b__mutmut_2: timeout; retry outcome: killed; "
        "timeout_multiplier=15 -> 30\n"
        "    a__mutmut_1: survived\n"
    )


def test_run_command_does_not_mutate_the_parent_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    seen: list[dict[str, str]] = []

    def stub_subprocess_run(
        command: Sequence[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        seen.append(dict(environment))
        return _completed()

    monkeypatch.setattr(mutation_gate.subprocess, "run", stub_subprocess_run)

    mutation_gate._run_command(("mutmut", "run"))

    assert seen[0]["PYTHONIOENCODING"] == "utf-8"
    assert "PYTHONIOENCODING" not in os.environ
