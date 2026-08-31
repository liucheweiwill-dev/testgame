import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.cards import Card, Rank, Suit, card_value
from domain.hand import hand_total, is_soft

cards = st.builds(
    Card, rank=st.sampled_from(tuple(Rank)), suit=st.sampled_from(tuple(Suit))
)
non_ace_cards = st.builds(
    Card,
    rank=st.sampled_from(tuple(rank for rank in Rank if rank is not Rank.ACE)),
    suit=st.sampled_from(tuple(Suit)),
)


@pytest.mark.property
@given(hand=st.lists(cards, min_size=1, max_size=10))
def test_hand_total_stays_between_hard_and_soft_sums(hand: list[Card]) -> None:
    hard_sum = sum(
        1 if card.rank is Rank.ACE else card_value(card.rank) for card in hand
    )
    soft_sum = sum(card_value(card.rank) for card in hand)

    assert hard_sum <= hand_total(hand) <= soft_sum


@pytest.mark.property
@given(hand=st.lists(non_ace_cards, min_size=1, max_size=10))
def test_hand_without_ace_is_hard_plain_sum(hand: list[Card]) -> None:
    assert is_soft(hand) is False
    assert hand_total(hand) == sum(card_value(card.rank) for card in hand)
