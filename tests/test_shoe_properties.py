from collections import Counter

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.cards import Card, Rank, Suit
from domain.shoe import Shoe


@pytest.mark.property
@given(seed=st.integers(), decks=st.integers(min_value=1, max_value=4))
def test_dealing_any_shoe_yields_canonical_multiset(seed: int, decks: int) -> None:
    shoe = Shoe(decks=decks, seed=seed)
    dealt = Counter(shoe.deal() for _ in range(shoe.remaining()))
    canonical = Counter({Card(rank, suit): decks for rank in Rank for suit in Suit})

    assert dealt == canonical
