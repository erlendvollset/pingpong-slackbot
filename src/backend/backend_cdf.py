import time
from dataclasses import asdict
from typing import Optional

from cognite.client import CogniteClient
from cognite.client.data_classes import Asset, Event, TimeSeries

from src.backend.backend import Backend
from src.backend.data_classes import Match, Player, Sport
from src.backend.rating import Ratings

STARTING_RATING = 1000
SPORT = "Sport"
MATCH = "Match"
HAND = "Hand"
RATINGS = "Ratings"


class BackendCdf(Backend):
    def __init__(self, root_asset_external_id: str, cognite_client: CogniteClient) -> None:
        self.root_asset_external_id = root_asset_external_id
        self.client = cognite_client

        self.root_asset = self.client.assets.retrieve(external_id=root_asset_external_id)
        if self.root_asset is None:
            self.root_asset = self.client.assets.create(
                Asset(external_id=root_asset_external_id, name=root_asset_external_id)
            )

    def wipe(self) -> None:
        time_series_to_delete = []
        for asset in self.client.assets(root_external_ids=[self.root_asset_external_id]):
            time_series_to_delete.extend([ts.id for ts in asset.time_series()])
        self.client.time_series.delete(time_series_to_delete)

        events_to_delete = [
            event.id for event in self.client.events(type=MATCH, root_asset_external_ids=[self.root_asset_external_id])
        ]
        self.client.events.delete(events_to_delete)

        self.client.assets.delete(external_id=self.root_asset_external_id, recursive=True)

    def create_player(self, player: Player) -> Player:
        asset = self.client.assets.create(
            Asset(
                external_id=player.id,
                name=player.name,
                parent_id=self.root_asset.id,
                metadata={RATINGS: Ratings().to_json()},
            )
        )
        return self._player_from_asset(asset)

    def get_players(self, ids: list[str]) -> list[Player]:
        return [self._player_from_asset(asset) for asset in self.client.assets.retrieve(external_id=ids)]

    def list_players(self) -> list[Player]:
        player_assets = self.client.assets.list(limit=-1, root_ids=[self.root_asset.id])
        return [self._player_from_asset(asset) for asset in player_assets]

    def _player_from_asset(self, asset: Asset) -> Player:
        return Player(asset.external_id, asset.name, Ratings.from_json(asset.metadata[RATINGS]))

    def update_player(self, id: str, name: Optional[str] = None, ratings: Optional[Ratings] = None) -> Player:
        player_asset = self.client.assets.retrieve(external_id=id)
        if name:
            player_asset.name = name
        if ratings:
            player_asset.metadata[RATINGS] = ratings.to_json()
            self._update_rating_time_series(id, player_asset.id, player_asset.name, ratings)
        updated_asset = self.client.assets.update(player_asset)
        return self._player_from_asset(updated_asset)

    def _update_rating_time_series(self, player_id: str, asset_id: int, name: str, ratings: Ratings) -> None:
        time_series = self.client.time_series.list(asset_external_ids=[player_id])
        ts_id_and_rating: list[tuple[int, int]] = []
        for hand, sport, rating in ratings:
            for ts in time_series:
                if ts.metadata.get(HAND) == hand.value and ts.metadata.get(SPORT) == sport.value:
                    ts_id_and_rating.append((ts.id, rating))
                    break
            else:
                new_ts = self.client.time_series.create(
                    TimeSeries(
                        name=f"{name} {sport.value} {hand} ELO",
                        asset_id=asset_id,
                        metadata={SPORT: sport.value, HAND: hand.value},
                    )
                )
                ts_id_and_rating.append((new_ts.id, rating))

        for ts_id, new_rating in ts_id_and_rating:
            self.client.datapoints.insert(id=ts_id, datapoints=[(int(time.time() * 1000), new_rating)])

    def create_match(self, match: Match) -> Match:
        event = self.client.events.create(Event(type=MATCH, subtype=match.sport.value, metadata=asdict(match)))
        return Match(**event.metadata)

    def get_matches(self, sport: Sport) -> list[Match]:
        events = self.client.events.list(limit=-1, type=MATCH, subtype=sport.value)
        return [Match(**e.metadata) for e in events]
