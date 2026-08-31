from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto

from domain.cards import Card
from domain.hand import hand_total, is_blackjack, is_bust, is_soft


class DealerRule(Enum):
    STAND_ON_SOFT_17 = auto()
    HIT_ON_SOFT_17 = auto()


class Outcome(Enum):
    PLAYER_BLACKJACK = auto()
    PLAYER_WINS = auto()
    DEALER_WINS = auto()
    PUSH = auto()


@dataclass(frozen=True)
class Settlement:
    outcome: Outcome
    returned: int


def dealer_should_hit(cards: Sequence[Card], rule: DealerRule) -> bool:
    total = hand_total(cards)
    return total < 17 or (
        total == 17 and is_soft(cards) and rule is DealerRule.HIT_ON_SOFT_17
    )


def settle(player: Sequence[Card], dealer: Sequence[Card], stake: int) -> Settlement:
    if not isinstance(stake, int):
        raise TypeError("stake must be an integer")
    if stake < 1:
        raise ValueError("stake must be positive")

    if is_bust(player):
        return Settlement(Outcome.DEALER_WINS, returned=0)

    player_blackjack = is_blackjack(player)
    dealer_blackjack = is_blackjack(dealer)
    if player_blackjack and dealer_blackjack:
        return Settlement(Outcome.PUSH, returned=stake)
    if player_blackjack:
        return Settlement(Outcome.PLAYER_BLACKJACK, returned=stake + stake * 3 // 2)
    if dealer_blackjack:
        return Settlement(Outcome.DEALER_WINS, returned=0)
    if is_bust(dealer):
        return Settlement(Outcome.PLAYER_WINS, returned=stake * 2)

    player_total = hand_total(player)
    dealer_total = hand_total(dealer)
    if player_total > dealer_total:
        return Settlement(Outcome.PLAYER_WINS, returned=stake * 2)
    if player_total < dealer_total:
        return Settlement(Outcome.DEALER_WINS, returned=0)
    return Settlement(Outcome.PUSH, returned=stake)
