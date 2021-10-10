from __future__ import annotations

import json
from typing import Any, Iterator, Optional

from src.backend.data_classes import Hand, Sport

INITIAL_RATING = 1000


class RatingCalculator:
    @staticmethod
    def calculate_new_elo_ratings(rating1: int, rating2: int, player1_win: bool) -> tuple[int, int]:
        t1 = 10 ** (rating1 / 400)
        t2 = 10 ** (rating2 / 400)
        e1 = t1 / (t1 + t2)
        e2 = t2 / (t1 + t2)
        s1 = 1 if player1_win else 0
        s2 = 0 if player1_win else 1
        new_rating1 = rating1 + int(round(32 * (s1 - e1)))
        new_rating2 = rating2 + int(round(32 * (s2 - e2)))
        return new_rating1, new_rating2


RatingDict = dict[Hand, dict[Sport, int]]


class Ratings:
    def __init__(self, ratings: Optional[RatingDict] = None):
        self._ratings: RatingDict = ratings or {}

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Ratings):
            return False
        return self._ratings == other._ratings

    def __iter__(self) -> Iterator[tuple[Hand, Sport, int]]:
        for hand in self._ratings:
            for sport, rating in self._ratings[hand].items():
                yield hand, sport, rating

    def update(self, hand: Hand, sport: Sport, rating: int) -> Ratings:
        return Ratings({**self._ratings, **{hand: {sport: rating}}})

    def get(self, hand: Hand, sport: Sport) -> int:
        if hand not in self._ratings or sport not in self._ratings[hand]:
            return INITIAL_RATING
        return self._ratings[hand][sport]

    @classmethod
    def from_json(self, s: str) -> Ratings:
        ratings_raw = json.loads(s)
        ratings: RatingDict = {}
        for hand in ratings_raw:
            ratings[Hand(hand)] = {}
            for sport, ranking in ratings_raw[hand].items():
                ratings[Hand(hand)].update({Sport(sport): int(ranking)})
        return Ratings(ratings)

    def to_json(self) -> str:
        ratings: dict[str, dict[str, int]] = {}
        for hand in self._ratings:
            ratings[hand.value] = {}
            for sport, ranking in self._ratings[hand].items():
                ratings[hand.value].update({sport.value: ranking})
        return json.dumps(ratings)
