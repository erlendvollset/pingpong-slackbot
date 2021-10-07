from dataclasses import dataclass

from pingpong.constants import DOMINANT, NON_DOMINANT, PING_PONG


class Player:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self._elo_ratings: dict[str, dict[str, int]] = {DOMINANT: {}, NON_DOMINANT: {}}

    def get_rating(self, sport: str = PING_PONG, hand: str = DOMINANT) -> int:
        return self._elo_ratings[hand].get(sport, 1000)

    def set_rating(self, elo_rating: int, sport: str = PING_PONG, hand: str = DOMINANT) -> None:
        self._elo_ratings[hand][sport] = elo_rating


@dataclass
class Match:
    player1_id: str
    player2_id: str
    player1_score: int
    player2_score: int
    player1_rating: int
    player2_rating: int
    sport: str = PING_PONG
    player1_hand: str = DOMINANT
    player2_hand: str = DOMINANT
