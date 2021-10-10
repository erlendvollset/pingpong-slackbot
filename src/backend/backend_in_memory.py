from copy import copy
from typing import Optional

from src.backend.backend import Backend
from src.backend.data_classes import Match, Player, Sport
from src.backend.rating import Ratings


class BackendInMemory(Backend):
    def __init__(self) -> None:
        self._players: list[Player] = []
        self._matches: list[Match] = []

    def wipe(self) -> None:
        self._players = []
        self._matches = []

    def create_player(self, player: Player) -> Player:
        self._players.append(player)
        return copy(player)

    def get_players(self, ids: list[str]) -> list[Player]:
        ids_set = set(ids)
        return list(filter(lambda p: p.id in ids_set, self._players))

    def list_players(self) -> list[Player]:
        return [p for p in self._players]

    def update_player(self, id: str, name: Optional[str] = None, ratings: Optional[Ratings] = None) -> Player:
        idx = [p.id for p in self._players].index(id)
        player = self._players[idx]
        if name:
            player.name = name
        if ratings:
            player.ratings = ratings
        self._players[idx] = player
        return copy(player)

    def create_match(self, match: Match) -> Match:
        self._matches.append(match)
        return copy(match)

    def list_matches(self, sport: Sport) -> list[Match]:
        return [match for match in self._matches if match.sport == sport]
