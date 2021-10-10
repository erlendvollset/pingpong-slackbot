import pytest
from _pytest.fixtures import SubRequest

from src.backend.backend import Backend
from src.backend.backend_in_memory import BackendInMemory
from src.backend.data_classes import Hand, Match, Player, Sport
from src.backend.rating import Ratings


@pytest.fixture(params=[BackendInMemory])
def backend(request: SubRequest) -> Backend:
    return request.param()


@pytest.fixture
def created_players(backend: Backend) -> list[Player]:
    p1 = backend.create_player(Player("id1", "name1", Ratings()))
    p2 = backend.create_player(Player("id2", "name2", Ratings()))
    return [p1, p2]


@pytest.fixture
def created_matches(backend: Backend, created_players: list[Player]) -> list[Match]:
    p1, p2 = created_players
    p1_rating = p1.ratings.get(Hand.DOMINANT, Sport.PING_PONG)
    p2_rating = p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG)
    match1 = backend.create_match(
        Match(
            player1_id=p1.id,
            player2_id=p2.id,
            player1_score=11,
            player2_score=0,
            player1_rating=p1_rating,
            player2_rating=p2_rating,
            sport=Sport.PING_PONG,
            player1_hand=Hand.DOMINANT,
            player2_hand=Hand.DOMINANT,
        )
    )
    match2 = backend.create_match(
        Match(
            player1_id=p1.id,
            player2_id=p2.id,
            player1_score=100,
            player2_score=200,
            player1_rating=p1_rating,
            player2_rating=p2_rating,
            sport=Sport.SQUASH,
            player1_hand=Hand.DOMINANT,
            player2_hand=Hand.DOMINANT,
        )
    )
    return [match1, match2]


class TestBackend:
    def test_create_player(self, backend: Backend) -> None:
        player = Player("id", "name", Ratings())
        created_player = backend.create_player(player)
        assert player == created_player

    def test_get_players(self, backend: Backend, created_players: list[Player]) -> None:
        res = backend.get_players([created_players[1].id])
        assert len(res) == 1
        assert res[0] == created_players[1]

    def test_list_players(self, backend: Backend, created_players: list[Player]) -> None:
        res = backend.list_players()
        assert len(res) == len(created_players)
        for p in res:
            assert p in created_players

    def test_update_player(self, backend: Backend, created_players: list[Player]) -> None:
        p1 = created_players[0]
        assert p1.ratings == Ratings()

        new_name = "newname"
        p1_name_updated = backend.update_player(id=p1.id, name=new_name)
        assert p1_name_updated.name == new_name
        assert p1_name_updated.ratings == Ratings()

        new_rating = p1.ratings.update(Hand.DOMINANT, Sport.PING_PONG, 2000)
        p1_ratings_updated = backend.update_player(id=p1.id, ratings=new_rating)
        assert p1_ratings_updated.name == new_name
        assert p1_ratings_updated.ratings == new_rating

    def test_create_match(self, backend: Backend, created_players: list[Player]) -> None:
        p1, p2 = created_players
        p1_rating = p1.ratings.get(Hand.DOMINANT, Sport.PING_PONG)
        p2_rating = p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG)
        match = Match(
            player1_id=p1.id,
            player2_id=p2.id,
            player1_score=11,
            player2_score=0,
            player1_rating=p1_rating,
            player2_rating=p2_rating,
            sport=Sport.PING_PONG,
            player1_hand=Hand.DOMINANT,
            player2_hand=Hand.DOMINANT,
        )
        created_match = backend.create_match(match)
        assert created_match == match

    def test_get_matches(self, backend: Backend, created_matches: list[Match]) -> None:
        res = backend.get_matches(sport=Sport.PING_PONG)
        assert len(res) == 1
        assert res[0] in created_matches

        res = backend.get_matches(sport=Sport.SQUASH)
        assert len(res) == 1
        assert res[0] in created_matches
