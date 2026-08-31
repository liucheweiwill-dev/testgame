from collections.abc import Sequence

from domain.cards import Card, Rank, card_value


def _total_and_soft(cards: Sequence[Card]) -> tuple[int, bool]:
    total = sum(card_value(card.rank) for card in cards)
    high_aces = sum(card.rank is Rank.ACE for card in cards)

    while total > 21 and high_aces:
        total -= 10
        high_aces -= 1

    return total, high_aces > 0


def hand_total(cards: Sequence[Card]) -> int:
    return _total_and_soft(cards)[0]


def is_soft(cards: Sequence[Card]) -> bool:
    return _total_and_soft(cards)[1]


def is_bust(cards: Sequence[Card]) -> bool:
    return hand_total(cards) > 21


def is_blackjack(cards: Sequence[Card]) -> bool:
    return len(cards) == 2 and hand_total(cards) == 21
