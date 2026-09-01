import hypothesis
from dataclasses import dataclass
from enum import Enum


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Suit(Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit


def card_value(rank: Rank) -> int:
    if rank is Rank.ACE:
        return 11
    return min(int(rank.value), 10)
