from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Sport(Enum):
    PING_PONG = "Ping-Pong"


class Hand(Enum):
    DOMINANT = "Dominant hand"
    NON_DOMINANT = "Non-dominant hand"


class Player:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self._elo_ratings: dict[Hand, dict[Sport, int]] = {Hand.DOMINANT: {}, Hand.NON_DOMINANT: {}}

    def get_rating(self, sport: Sport, hand: Hand = Hand.DOMINANT) -> int:
        return self._elo_ratings[hand].get(sport, 1000)

    def set_rating(self, elo_rating: int, sport: Sport, hand: Hand = Hand.DOMINANT) -> None:
        self._elo_ratings[hand][sport] = elo_rating


@dataclass
class Match:
    player1_id: str
    player2_id: str
    player1_score: int
    player2_score: int
    player1_rating: int
    player2_rating: int
    sport: Sport
    player1_hand: Hand
    player2_hand: Hand
