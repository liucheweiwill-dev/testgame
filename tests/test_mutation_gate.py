from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

import pytest
from tools import mutation_gate

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
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


# The gate's own gauntlet-scope scenarios.
def _project_and_workflow_text() -> tuple[str, str]:
    return (
        (REPOSITORY_ROOT / "PROJECT.md").read_text(encoding="utf-8"),
        (REPOSITORY_ROOT / ".github/workflows/gauntlet.yml").read_text(
            encoding="utf-8"
        ),
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
    config = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert config["tool"]["mutmut"]["source_paths"] == ["src/domain", "tools"]


def test_gate_test_runs_in_normal_test_suite() -> None:
    config = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert config["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert Path(__file__).parent.name == "tests"


# Deprecation-removal scenarios.
def test_mutmut_configuration_uses_source_paths_not_paths_to_mutate() -> None:
    config = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["tool"]["mutmut"]

    assert "paths_to_mutate" not in config
    assert config["source_paths"] == ["src/domain", "tools"]


def test_mutation_step_invokes_gate_in_project_and_workflow() -> None:
    project, workflow = _project_and_workflow_text()
    command = "uv run python tools/mutation_gate.py"

    assert command in project
    assert command in workflow


def test_vulture_configuration_includes_tools() -> None:
    config = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

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
        [sys.executable, str(REPOSITORY_ROOT / "tools/mutation_gate.py")],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "domain.x.y__mutmut_1: survived" in completed.stdout
