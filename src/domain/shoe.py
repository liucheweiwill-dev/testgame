import random

from domain.cards import Card, Rank, Suit


class ShoeExhausted(Exception):
    pass


class Shoe:
    def __init__(self, decks: int, seed: int) -> None:
        if decks < 1:
            raise ValueError("decks must be at least 1")

        self._cards = [
            Card(rank, suit)
            for _ in range(decks)
            for rank in Rank
            for suit in Suit
        ]
        random.Random(seed).shuffle(self._cards)

    def deal(self) -> Card:
        if not self._cards:
            raise ShoeExhausted
        return self._cards.pop()

    def remaining(self) -> int:
        return len(self._cards)
