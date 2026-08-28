from domain.cards import Card, Rank, Suit, card_value


def test_card_values_two_through_ten() -> None:
    expected = {
        Rank.TWO: 2,
        Rank.THREE: 3,
        Rank.FOUR: 4,
        Rank.FIVE: 5,
        Rank.SIX: 6,
        Rank.SEVEN: 7,
        Rank.EIGHT: 8,
        Rank.NINE: 9,
        Rank.TEN: 10,
    }

    assert {rank: card_value(rank) for rank in expected} == expected


def test_card_values_face_cards() -> None:
    assert card_value(Rank.JACK) == 10
    assert card_value(Rank.QUEEN) == 10
    assert card_value(Rank.KING) == 10


def test_card_value_ace() -> None:
    assert card_value(Rank.ACE) == 11


def test_card_is_frozen() -> None:
    card = Card(Rank.ACE, Suit.SPADES)

    try:
        card.rank = Rank.TWO
    except AttributeError:
        pass
    else:
        raise AssertionError("Card must be immutable")
