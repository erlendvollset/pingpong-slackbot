from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.backend.util import BaseEnum

if TYPE_CHECKING:
    from src.backend.rating import Ratings


class Sport(BaseEnum):
    PING_PONG = "Ping-Pong"
    SQUASH = "Squash"


class Hand(BaseEnum):
    DOMINANT = "Dominant hand"
    NON_DOMINANT = "Non-dominant hand"


@dataclass
class Player:
    id: str
    name: str
    ratings: Ratings


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
