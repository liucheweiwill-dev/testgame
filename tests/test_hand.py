from domain.cards import Card, Rank, Suit
from domain.hand import hand_total, is_blackjack, is_bust, is_soft


def _cards(*ranks: Rank) -> list[Card]:
    suits = tuple(Suit)
    return [Card(rank, suits[index % len(suits)]) for index, rank in enumerate(ranks)]


def test_hand_total_ace_king_is_soft_twenty_one() -> None:
    cards = _cards(Rank.ACE, Rank.KING)

    assert hand_total(cards) == 21
    assert is_soft(cards) is True


def test_hand_total_ace_six_is_soft_seventeen() -> None:
    cards = _cards(Rank.ACE, Rank.SIX)

    assert hand_total(cards) == 17
    assert is_soft(cards) is True


def test_hand_total_ace_six_king_is_hard_seventeen() -> None:
    cards = _cards(Rank.ACE, Rank.SIX, Rank.KING)

    assert hand_total(cards) == 17
    assert is_soft(cards) is False


def test_hand_total_two_aces_is_soft_twelve() -> None:
    cards = _cards(Rank.ACE, Rank.ACE)

    assert hand_total(cards) == 12
    assert is_soft(cards) is True


def test_hand_total_three_aces_is_soft_thirteen() -> None:
    cards = _cards(Rank.ACE, Rank.ACE, Rank.ACE)

    assert hand_total(cards) == 13
    assert is_soft(cards) is True


def test_hand_total_two_aces_nine_is_soft_twenty_one() -> None:
    cards = _cards(Rank.ACE, Rank.ACE, Rank.NINE)

    assert hand_total(cards) == 21
    assert is_soft(cards) is True


def test_hand_total_king_queen_five_is_hard_twenty_five() -> None:
    cards = _cards(Rank.KING, Rank.QUEEN, Rank.FIVE)

    assert hand_total(cards) == 25
    assert is_soft(cards) is False


def test_empty_hand_total_is_hard_zero() -> None:
    assert hand_total([]) == 0
    assert is_soft([]) is False


def test_blackjack_ace_then_king() -> None:
    assert is_blackjack(_cards(Rank.ACE, Rank.KING)) is True


def test_blackjack_king_then_ace() -> None:
    assert is_blackjack(_cards(Rank.KING, Rank.ACE)) is True


def test_blackjack_ace_then_ten() -> None:
    assert is_blackjack(_cards(Rank.ACE, Rank.TEN)) is True


def test_three_card_twenty_one_is_not_blackjack() -> None:
    assert is_blackjack(_cards(Rank.ACE, Rank.NINE, Rank.ACE)) is False


def test_total_above_twenty_one_is_bust() -> None:
    assert is_bust(_cards(Rank.KING, Rank.QUEEN, Rank.FIVE)) is True


def test_total_of_twenty_one_is_not_bust() -> None:
    assert is_bust(_cards(Rank.ACE, Rank.KING)) is False
