import time
from dataclasses import asdict
from typing import List

from cognite.client.data_classes import Asset, TimeSeries, Event
from cognite.experimental import CogniteClient

from src.constants import SPORT, HAND, STARTING_RATING, DOMINANT, MATCH, ROOT_ASSET_EXTERNAL_ID
from src.models import Player, Match


class CDFBackend:
    def __init__(self, sport):
        self.client = CogniteClient()
        self.sport = sport
        self.root_asset = self.client.assets.retrieve(external_id=ROOT_ASSET_EXTERNAL_ID)
        if self.root_asset is None:
            self.root_asset = self.client.assets.create(Asset(external_id=ROOT_ASSET_EXTERNAL_ID, name=ROOT_ASSET_EXTERNAL_ID))

    def create_player(self, player: Player):
        self.client.assets.create(Asset(external_id=player.get_id(), name=player.get_name(), root_id=self.root_asset.id))

    def get_players(self, ids: List[str] = None) -> List[Player]:
        ids = set(ids)
        player_assets = self.client.assets.list(limit=-1, root_ids=[self.root_asset.id])
        if ids is not None:
            player_assets = [a for a in player_assets if a.id in ids]
        return [self._player_from_asset(asset) for asset in player_assets]

    def _player_from_asset(self, asset: Asset):
        player = Player(asset.id, asset.name)
        time_series = self.client.time_series.list(asset_external_ids=[player.get_id()])
        for ts in time_series:
            if ts.metadata.get(SPORT) != self.sport:
                continue
            hand = ts.metadata.get(HAND)
            if hand is not None:
                last_data_point = self.client.datapoints.retrieve_latest(id=ts.id)
                if not last_data_point.value:
                    rating = STARTING_RATING
                else:
                    rating = last_data_point.value[0]
                player.set_rating(rating, self.sport, hand)

    def update_player(self, id: str, new_name=None, new_rating=None, hand: str = DOMINANT):
        player_asset = self.client.assets.retrieve(external_id=id)
        if new_name:
            player_asset.name = new_name
            self.client.assets.update(player_asset)
        if new_rating is not None:
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
                        metadata={SPORT: self.sport, HAND: hand}
                    )
                )
            self.client.datapoints.insert(datapoints=[{int(time.time()*1000): new_rating}], id=rating_time_series.id)

    def create_match(self, match: Match):
        self.client.events.create(Event(type=MATCH, subtype=match.sport, metadata=asdict(match)))

    def get_matches(self) -> List[Match]:
        events = self.client.events.list(limit=-1, type=MATCH, subtype=self.sport)
        return [Match(**e.metadata) for e in events]
