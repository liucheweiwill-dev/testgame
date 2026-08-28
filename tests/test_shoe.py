import random
from collections import Counter

import pytest

from domain.cards import Card, Rank, Suit
from domain.shoe import Shoe, ShoeExhausted


def _deal_all(shoe: Shoe) -> list[Card]:
    return [shoe.deal() for _ in range(shoe.remaining())]


def test_six_deck_shoe_starts_with_312_cards() -> None:
    assert Shoe(decks=6, seed=42).remaining() == 312


def test_six_deck_shoe_has_six_of_every_rank_suit_pair() -> None:
    dealt = Counter(_deal_all(Shoe(decks=6, seed=42)))
    canonical = Counter({Card(rank, suit): 6 for rank in Rank for suit in Suit})

    assert dealt == canonical


def test_same_seed_deals_identical_sequences() -> None:
    first = _deal_all(Shoe(decks=6, seed=42))
    second = _deal_all(Shoe(decks=6, seed=42))

    assert first == second


def test_different_seeds_deal_different_sequences() -> None:
    first = _deal_all(Shoe(decks=6, seed=42))
    second = _deal_all(Shoe(decks=6, seed=43))

    assert first != second


def test_remaining_decreases_and_313th_deal_raises() -> None:
    shoe = Shoe(decks=6, seed=42)

    for expected_remaining in range(311, -1, -1):
        shoe.deal()
        assert shoe.remaining() == expected_remaining

    with pytest.raises(ShoeExhausted):
        shoe.deal()


def test_shoe_rejects_zero_decks() -> None:
    with pytest.raises(ValueError):
        Shoe(decks=0, seed=1)


def test_shoe_rejects_negative_decks() -> None:
    with pytest.raises(ValueError):
        Shoe(decks=-1, seed=1)


def test_exhausting_shoe_leaves_global_random_state_unchanged() -> None:
    original_state = random.getstate()

    _deal_all(Shoe(decks=6, seed=42))

    assert random.getstate() == original_state
