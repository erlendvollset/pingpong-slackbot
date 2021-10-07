from dataclasses import dataclass

from pingpong.constants import PING_PONG, DOMINANT, NON_DOMINANT


class Player():
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.elo_ratings = {DOMINANT: {}, NON_DOMINANT: {}}

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_rating(self, sport: str=PING_PONG, hand=DOMINANT):
        return self.elo_ratings[hand].get(sport, 1000)

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_rating(self, elo_rating, sport: str=PING_PONG, hand=DOMINANT):
        self.elo_ratings[hand][sport] = elo_rating


@dataclass
class Match():
    player1_id: str
    player2_id: str
    player1_score: int
    player2_score: int
    player1_rating: int
    player2_rating: int
    sport: str = PING_PONG
    player1_hand: str = DOMINANT
    player2_hand: str = DOMINANT
