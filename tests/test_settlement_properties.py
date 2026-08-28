import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.cards import Card, Rank, Suit
from domain.hand import hand_total, is_blackjack, is_bust
from domain.settlement import Outcome, settle

cards = st.builds(
    Card, rank=st.sampled_from(tuple(Rank)), suit=st.sampled_from(tuple(Suit))
)
hands = st.lists(cards, max_size=6)


@pytest.mark.property
@given(player=hands, dealer=hands, stake=st.integers(min_value=0, max_value=1000))
def test_settlement_pushes_exactly_for_defined_ties(
    player: list[Card], dealer: list[Card], stake: int
) -> None:
    both_blackjack = is_blackjack(player) and is_blackjack(dealer)
    equal_live_non_blackjack = (
        not is_blackjack(player)
        and not is_blackjack(dealer)
        and not is_bust(player)
        and not is_bust(dealer)
        and hand_total(player) == hand_total(dealer)
    )

    assert (settle(player, dealer, stake).outcome is Outcome.PUSH) == (
        both_blackjack or equal_live_non_blackjack
    )
