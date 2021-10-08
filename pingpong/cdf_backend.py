import time
from dataclasses import asdict
from typing import Optional

from cognite.client import CogniteClient
from cognite.client.data_classes import Asset, Event, TimeSeries

from pingpong.data_classes import Hand, Match, Player, Sport

STARTING_RATING = 1000
SPORT = "Sport"
MATCH = "Match"
HAND = "Hand"


class CDFBackend:
    def __init__(self, sport: Sport, root_asset_external_id: str, cognite_client: CogniteClient) -> None:
        self.sport = sport
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

        events_to_delete = [event.id for event in self.client.events(type=MATCH, subtype=self.sport)]
        self.client.events.delete(events_to_delete)

        self.client.assets.delete(external_id=self.root_asset_external_id, recursive=True)

    def create_player(self, player: Player) -> None:
        self.client.assets.create(Asset(external_id=player.id, name=player.name, parent_id=self.root_asset.id))

    def get_players(self, ids: list[str]) -> list[Player]:
        return [self._player_from_asset(asset) for asset in self.client.assets.retrieve(external_id=ids)]

    def list_players(self) -> list[Player]:
        player_assets = self.client.assets.list(limit=-1, root_ids=[self.root_asset.id])
        return [self._player_from_asset(asset) for asset in player_assets]

    def _player_from_asset(self, asset: Asset) -> Player:
        player = Player(asset.external_id, asset.name)
        time_series = self.client.time_series.list(asset_external_ids=[player.id])
        for ts in time_series:
            if ts.metadata.get(SPORT) != self.sport.value:
                continue
            hand = ts.metadata.get(HAND)
            if hand is not None:
                last_data_point = self.client.datapoints.retrieve_latest(id=ts.id)
                if not last_data_point.value:
                    rating = STARTING_RATING
                else:
                    rating = last_data_point.value[0]
                player.set_rating(rating, self.sport, hand)
        return player

    def update_player(
        self, id: str, new_name: Optional[str] = None, new_rating: Optional[int] = None, hand: Hand = Hand.DOMINANT
    ) -> Player:
        player_asset = self.client.assets.retrieve(external_id=id)
        if new_name:
            player_asset.name = new_name
        if new_rating is not None:
            player_asset.metadata = player_asset.metadata.update({"rating": str(new_rating)})
            time_series = self.client.time_series.list(asset_external_ids=[id])
            time_series = [
                ts for ts in time_series if ts.metadata.get(HAND) == hand and ts.metadata.get(SPORT) == self.sport
            ]
            if time_series:
                rating_time_series = time_series[0]
            else:
                rating_time_series = self.client.time_series.create(
                    TimeSeries(
                        name=f"{player_asset.name} {self.sport} {hand} ELO",
                        asset_id=player_asset.id,
                        metadata={SPORT: self.sport.value, HAND: hand.value},
                    )
                )
            self.client.datapoints.insert(
                datapoints=[(int(time.time() * 1000), new_rating)],
                id=rating_time_series.id,
            )
        updated_asset = self.client.assets.update(player_asset)
        return self._player_from_asset(updated_asset)

    def create_match(self, match: Match) -> None:
        self.client.events.create(Event(type=MATCH, subtype=match.sport.value, metadata=asdict(match)))

    def get_matches(self) -> list[Match]:
        events = self.client.events.list(limit=-1, type=MATCH, subtype=self.sport)
        return [Match(**e.metadata) for e in events]
