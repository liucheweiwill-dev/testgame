from domain.scaffold import is_bust


def test_twenty_one_is_not_bust() -> None:
    assert is_bust(21) is False


def test_twenty_two_is_bust() -> None:
    assert is_bust(22) is True
