from abc import ABC, abstractmethod
from typing import Optional

from src.backend.data_classes import Match, Player, Sport
from src.backend.rating import Ratings


class Backend(ABC):
    @abstractmethod
    def wipe(self) -> None:
        ...

    @abstractmethod
    def create_player(self, player: Player) -> Player:
        ...

    @abstractmethod
    def get_players(self, ids: list[str]) -> list[Player]:
        ...

    @abstractmethod
    def list_players(self) -> list[Player]:
        ...

    @abstractmethod
    def update_player(self, id: str, name: Optional[str] = None, ratings: Optional[Ratings] = None) -> Player:
        ...

    @abstractmethod
    def create_match(self, match: Match) -> Match:
        ...

    @abstractmethod
    def list_matches(self, sport: Sport) -> list[Match]:
        ...
