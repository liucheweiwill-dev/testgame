"""Toolchain scaffolding — task 001 deletes this file.

It exists only so the gauntlet has something to run against before any real
domain code is written. Every layer is exercised here on purpose: the function
is covered, typed, mutated and property-tested, so that a red layer during
bootstrap means the toolchain is wrong rather than the domain.

The Cleanup layer will flag this file once nothing imports it, which is the
signal that task 001 finished the job.
"""


def is_bust(total: int) -> bool:
    """True when a hand total has gone past 21."""
    return total > 21
