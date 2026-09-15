from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

type ParsedResult = tuple[str, str]
type CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]

_FAILURE_STATUSES = frozenset(
    {
        "survived",
        "no tests",
        "not checked",
        "skipped",
        "suspicious",
        "caught by type check",
        "segfault",
        "check was interrupted by user",
    }
)
_KNOWN_STATUSES = _FAILURE_STATUSES | {"timeout"}
_MUTANT_SUMMARY = re.compile(r"(\d+)/(\d+)\s+🎉")
_RETRY_BUDGET = re.compile(
    r"^mutation-gate retry budget: timeout_multiplier="
    r"(?P<initial>[-+0-9.eE]+) -> (?P<retry>[-+0-9.eE]+)$",
    re.MULTILINE,
)
_RETRY_FACTOR = 2.0
_RETRY_PROGRAM = """\
import sys
from mutmut.configuration import Config

config = Config.get()
initial = float(config.timeout_multiplier)
retry = initial * float(sys.argv[1])
if retry <= initial:
    raise SystemExit("mutation-gate retry budget did not increase")
config.timeout_multiplier = retry
print(
    "mutation-gate retry budget: "
    f"timeout_multiplier={initial:g} -> {retry:g}"
)

from mutmut.__main__ import cli

cli.main(
    args=["run", "--max-children", "1", sys.argv[2]],
    prog_name="mutmut",
)
"""


class GateError(ValueError):
    pass


def parse_results(output: str) -> list[ParsedResult]:
    parsed: list[ParsedResult] = []
    seen_mutants: set[str] = set()

    for line in output.splitlines():
        if not line.strip():
            continue
        if not line.startswith("    ") or line.startswith("     "):
            raise GateError(f"malformed mutmut results line: {line!r}")

        mutant, separator, status = line[4:].partition(": ")
        if not separator or not mutant or not status or status != status.strip():
            raise GateError(f"malformed mutmut results line: {line!r}")
        if status not in _KNOWN_STATUSES:
            raise GateError(f"unrecognised status {status!r} for mutant {mutant!r}")
        if mutant in seen_mutants:
            raise GateError(f"duplicate mutmut results line for mutant {mutant!r}")

        seen_mutants.add(mutant)
        parsed.append((mutant, status))

    return parsed


def _configured_mutmut_command() -> tuple[str, ...]:
    raw_command = os.environ.get("MUTATION_GATE_MUTMUT_COMMAND")
    if raw_command is None:
        return ("mutmut",)

    try:
        command = json.loads(raw_command)
    except json.JSONDecodeError as error:
        raise GateError(
            "MUTATION_GATE_MUTMUT_COMMAND must be a JSON array of strings"
        ) from error

    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise GateError(
            "MUTATION_GATE_MUTMUT_COMMAND must be a non-empty JSON array "
            "of non-empty strings"
        )
    return tuple(command)


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        check=False,
    )


def _invoke(
    runner: CommandRunner,
    command: Sequence[str],
    label: str,
    output: TextIO,
) -> subprocess.CompletedProcess[str] | None:
    try:
        return runner(command)
    except OSError as error:
        output.write(f"{label} failed to start: {error}\n")
        return None


def _producer_succeeded(
    label: str,
    completed: subprocess.CompletedProcess[str] | None,
    output: TextIO,
) -> bool:
    if completed is None:
        return False
    if completed.returncode == 0:
        return True

    output.write(f"{label} failed with exit code {completed.returncode}\n")
    if completed.stdout:
        output.write(completed.stdout)
        if not completed.stdout.endswith("\n"):
            output.write("\n")
    if completed.stderr:
        output.write(completed.stderr)
        if not completed.stderr.endswith("\n"):
            output.write("\n")
    return False


def _generated_mutant_count(run_output: str) -> int:
    matches = list(_MUTANT_SUMMARY.finditer(run_output))
    if not matches:
        raise GateError("could not read the generated-mutant count from mutmut run")
    return int(matches[-1].group(2))


def _retry_command(mutant: str) -> tuple[str, ...]:
    return (
        sys.executable,
        "-c",
        _RETRY_PROGRAM,
        str(_RETRY_FACTOR),
        mutant,
    )


def _retry_budget(run_output: str) -> str:
    matches = list(_RETRY_BUDGET.finditer(run_output))
    if len(matches) != 1:
        raise GateError("timeout retry did not report exactly one raised budget")

    initial = float(matches[0].group("initial"))
    retry = float(matches[0].group("retry"))
    if retry <= initial:
        raise GateError(
            "timeout retry budget was not raised: "
            f"timeout_multiplier={initial:g} -> {retry:g}"
        )
    return f"timeout_multiplier={initial:g} -> {retry:g}"


def _print_messages(messages: Sequence[str], output: TextIO) -> None:
    for message in messages:
        output.write(message)
        if not message.endswith("\n"):
            output.write("\n")


def run_gate(
    *,
    runner: CommandRunner,
    output: TextIO,
) -> int:
    try:
        mutmut_command = _configured_mutmut_command()
    except GateError as error:
        output.write(f"mutation gate failed: {error}\n")
        return 1

    initial_run = _invoke(runner, (*mutmut_command, "run"), "mutmut run", output)
    if not _producer_succeeded("mutmut run", initial_run, output):
        return 1
    assert initial_run is not None

    results_run = _invoke(
        runner, (*mutmut_command, "results"), "mutmut results", output
    )
    if not _producer_succeeded("mutmut results", results_run, output):
        return 1
    assert results_run is not None

    try:
        mutant_count = _generated_mutant_count(initial_run.stdout)
        initial_results = parse_results(results_run.stdout)
    except GateError as error:
        output.write(f"mutation gate failed: {error}\n")
        return 1

    if mutant_count == 0:
        output.write("mutation gate failed: no mutants were generated\n")
        return 1

    failures = [
        f"    {mutant}: {status}"
        for mutant, status in initial_results
        if status in _FAILURE_STATUSES
    ]
    retry_notes: list[str] = []

    for mutant, status in initial_results:
        if status != "timeout":
            continue

        retry_run = _invoke(
            runner,
            _retry_command(mutant),
            f"mutmut retry for {mutant}",
            output,
        )
        if not _producer_succeeded(f"mutmut retry for {mutant}", retry_run, output):
            retry_notes.append(f"    {mutant}: timeout; retry producer failed")
            _print_messages((*retry_notes, *failures), output)
            return 1
        assert retry_run is not None

        try:
            budget = _retry_budget(retry_run.stdout)
        except GateError as error:
            retry_notes.append(f"    {mutant}: timeout; retry budget invalid")
            _print_messages((*retry_notes, *failures), output)
            output.write(f"mutation gate failed: {error}\n")
            return 1

        retry_results_run = _invoke(
            runner,
            (*mutmut_command, "results"),
            "mutmut results after retry",
            output,
        )
        if not _producer_succeeded(
            "mutmut results after retry", retry_results_run, output
        ):
            retry_notes.append(
                f"    {mutant}: timeout; retry result producer failed; {budget}"
            )
            _print_messages((*retry_notes, *failures), output)
            return 1
        assert retry_results_run is not None

        try:
            retry_results = dict(parse_results(retry_results_run.stdout))
        except GateError as error:
            retry_notes.append(
                f"    {mutant}: timeout; retry result malformed; {budget}"
            )
            _print_messages((*retry_notes, *failures), output)
            output.write(f"mutation gate failed: {error}\n")
            return 1

        retry_status = retry_results.get(mutant, "killed")
        if retry_status == "timeout":
            retry_notes.append(
                f"    {mutant}: timeout; retry outcome: timeout "
                f"(counted as killed); {budget}"
            )
        elif retry_status == "killed":
            retry_notes.append(
                f"    {mutant}: timeout; retry outcome: killed; {budget}"
            )
        else:
            retry_notes.append(
                f"    {mutant}: timeout; retry outcome: {retry_status}; {budget}"
            )
            failures.append(f"    {mutant}: {retry_status}")

    _print_messages((*retry_notes, *failures), output)
    if failures:
        return 1

    output.write(f"mutation gate passed: {mutant_count} mutants generated\n")
    return 0


def main() -> int:
    return run_gate(runner=_run_command, output=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
