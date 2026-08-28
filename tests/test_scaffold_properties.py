import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.scaffold import is_bust


@pytest.mark.property
@given(total=st.integers(max_value=21))
def test_never_bust_at_or_below_twenty_one(total: int) -> None:
    assert is_bust(total) is False


@pytest.mark.property
@given(total=st.integers(min_value=22))
def test_always_bust_above_twenty_one(total: int) -> None:
    assert is_bust(total) is True
