from domain.cards import Card, Rank, Suit
from domain.settlement import (
    DealerRule,
    Outcome,
    Settlement,
    dealer_should_hit,
    settle,
)


def _cards(*ranks: Rank) -> list[Card]:
    suits = tuple(Suit)
    return [Card(rank, suits[index % len(suits)]) for index, rank in enumerate(ranks)]


def test_dealer_hard_seventeen_stands_under_s17() -> None:
    assert (
        dealer_should_hit(
            _cards(Rank.KING, Rank.SEVEN), DealerRule.STAND_ON_SOFT_17
        )
        is False
    )


def test_dealer_hard_seventeen_stands_under_h17() -> None:
    assert (
        dealer_should_hit(_cards(Rank.KING, Rank.SEVEN), DealerRule.HIT_ON_SOFT_17)
        is False
    )


def test_dealer_soft_seventeen_stands_under_s17() -> None:
    assert (
        dealer_should_hit(_cards(Rank.ACE, Rank.SIX), DealerRule.STAND_ON_SOFT_17)
        is False
    )


def test_dealer_soft_seventeen_hits_under_h17() -> None:
    assert (
        dealer_should_hit(_cards(Rank.ACE, Rank.SIX), DealerRule.HIT_ON_SOFT_17)
        is True
    )


def test_dealer_sixteen_hits_under_either_rule() -> None:
    cards = _cards(Rank.KING, Rank.SIX)

    assert dealer_should_hit(cards, DealerRule.STAND_ON_SOFT_17) is True
    assert dealer_should_hit(cards, DealerRule.HIT_ON_SOFT_17) is True


def test_dealer_eighteen_stands_under_either_rule() -> None:
    cards = _cards(Rank.KING, Rank.EIGHT)

    assert dealer_should_hit(cards, DealerRule.STAND_ON_SOFT_17) is False
    assert dealer_should_hit(cards, DealerRule.HIT_ON_SOFT_17) is False


def test_both_blackjack_pushes() -> None:
    result = settle(
        _cards(Rank.ACE, Rank.KING), _cards(Rank.ACE, Rank.QUEEN), stake=10
    )

    assert result == Settlement(Outcome.PUSH, returned=10)


def test_blackjack_beats_three_card_twenty_one() -> None:
    result = settle(
        _cards(Rank.ACE, Rank.KING),
        _cards(Rank.SEVEN, Rank.SEVEN, Rank.SEVEN),
        stake=10,
    )

    assert result == Settlement(Outcome.PLAYER_BLACKJACK, returned=25)


def test_blackjack_beats_twenty() -> None:
    result = settle(
        _cards(Rank.ACE, Rank.KING), _cards(Rank.KING, Rank.QUEEN), stake=10
    )

    assert result == Settlement(Outcome.PLAYER_BLACKJACK, returned=25)


def test_blackjack_odd_stake_five_truncates_payout() -> None:
    result = settle(
        _cards(Rank.ACE, Rank.KING), _cards(Rank.KING, Rank.QUEEN), stake=5
    )

    assert result == Settlement(Outcome.PLAYER_BLACKJACK, returned=12)


def test_blackjack_stake_one_returns_only_stake() -> None:
    result = settle(
        _cards(Rank.ACE, Rank.KING), _cards(Rank.KING, Rank.QUEEN), stake=1
    )

    assert result == Settlement(Outcome.PLAYER_BLACKJACK, returned=1)


def test_dealer_blackjack_beats_player_twenty() -> None:
    result = settle(
        _cards(Rank.KING, Rank.QUEEN), _cards(Rank.ACE, Rank.KING), stake=10
    )

    assert result == Settlement(Outcome.DEALER_WINS, returned=0)


def test_player_twenty_beats_dealer_nineteen() -> None:
    result = settle(
        _cards(Rank.KING, Rank.QUEEN), _cards(Rank.KING, Rank.NINE), stake=10
    )

    assert result == Settlement(Outcome.PLAYER_WINS, returned=20)


def test_player_nineteen_loses_to_dealer_twenty() -> None:
    result = settle(
        _cards(Rank.KING, Rank.NINE), _cards(Rank.KING, Rank.QUEEN), stake=10
    )

    assert result == Settlement(Outcome.DEALER_WINS, returned=0)


def test_equal_twenty_pushes() -> None:
    result = settle(
        _cards(Rank.KING, Rank.QUEEN), _cards(Rank.JACK, Rank.QUEEN), stake=10
    )

    assert result == Settlement(Outcome.PUSH, returned=10)


def test_player_bust_loses_even_when_dealer_busts_higher() -> None:
    result = settle(
        _cards(Rank.KING, Rank.QUEEN, Rank.TWO),
        _cards(Rank.KING, Rank.QUEEN, Rank.THREE),
        stake=10,
    )

    assert result == Settlement(Outcome.DEALER_WINS, returned=0)


def test_player_eighteen_beats_busted_dealer() -> None:
    result = settle(
        _cards(Rank.KING, Rank.EIGHT),
        _cards(Rank.KING, Rank.QUEEN, Rank.FOUR),
        stake=10,
    )

    assert result == Settlement(Outcome.PLAYER_WINS, returned=20)
