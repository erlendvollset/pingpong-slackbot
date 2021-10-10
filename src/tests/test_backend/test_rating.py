import json

from src.backend.data_classes import Hand, Sport
from src.backend.rating import RatingCalculator, Ratings


def test_rating_calculator() -> None:
    assert 1016, 984 == RatingCalculator.calculate_new_elo_ratings(1000, 1000, True)
    assert 984, 1016 == RatingCalculator.calculate_new_elo_ratings(1000, 1000, False)
    assert 2000, 0 == RatingCalculator.calculate_new_elo_ratings(2000, 0, True)


class TestRatings:
    def test_get_rating_does_not_exist(self) -> None:
        r = Ratings()
        assert r.get(Hand.DOMINANT, Sport.PING_PONG) == 1000

    def test_get_rating(self) -> None:
        r = Ratings({Hand.DOMINANT: {Sport.PING_PONG: 1500}})
        assert r.get(Hand.DOMINANT, Sport.PING_PONG) == 1500

    def test_update_rating(self) -> None:
        r = Ratings({Hand.DOMINANT: {Sport.PING_PONG: 1500}})
        r_updated = r.update(Hand.DOMINANT, Sport.PING_PONG, 2000)
        assert r.get(Hand.DOMINANT, Sport.PING_PONG) == 1500
        assert r_updated.get(Hand.DOMINANT, Sport.PING_PONG) == 2000

    def test_ratings_to_json(self) -> None:
        r = Ratings({Hand.DOMINANT: {Sport.PING_PONG: 1500}})
        assert r.to_json() == json.dumps({Hand.DOMINANT.value: {Sport.PING_PONG.value: 1500}})

    def test_ratings_from_json(self) -> None:
        expected = Ratings({Hand.DOMINANT: {Sport.PING_PONG: 1500}})
        json_str = json.dumps({Hand.DOMINANT.value: {Sport.PING_PONG.value: 1500}})
        assert Ratings.from_json(json_str) == expected

    def test_iter_ratings(self) -> None:
        ratings = Ratings(
            {Hand.DOMINANT: {Sport.PING_PONG: 1500, Sport.SQUASH: 2000}, Hand.NON_DOMINANT: {Sport.PING_PONG: 1200}}
        )
        expected = {
            (Hand.DOMINANT, Sport.SQUASH, 2000),
            (Hand.DOMINANT, Sport.PING_PONG, 1500),
            (Hand.NON_DOMINANT, Sport.PING_PONG, 1200),
        }
        assert set(ratings) == expected
