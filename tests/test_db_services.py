import os
import sys
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(src_dir)
os.environ["DATABASE_URL"] = "blabla"
from unittest import mock
import pytest
import services.db_services
from models.Player import Player
from services import db_services

@pytest.fixture()
def cursor_mock(monkeypatch):
    connection_mock = mock.MagicMock()
    cursor_mock = mock.MagicMock()
    def mock_return():
        return connection_mock, cursor_mock
    monkeypatch.setattr(services.db_services, "connect", mock_return)
    yield cursor_mock

def test_add_match_result(cursor_mock):
    cursor_mock.fetchone.side_effect = [("erlend", 1000, 1), ("ola", 1000, 2)]
    res = db_services.add_match_result(1, False, 2, False, 11, 0)
    assert res == (1016, 984, 16, -16)

def test_add_match_result_invalid_player(cursor_mock):
    cursor_mock.fetchone.side_effect = [None, ("ola", 1000, 2)]
    res = db_services.add_match_result(1, False, 2, False, 11, 0)
    assert res == (None, None, None, None)

def test_get_player(cursor_mock):
    cursor_mock.fetchone.side_effect = [(1, "erlend", 1000)]
    p = db_services.get_player(1)
    assert p.get_name() == "erlend"
    assert p.get_id() == 1
    assert p.get_rating() == 1000

def test_get_player_invalid_id(cursor_mock):
    cursor_mock.fetchone.return_value = None
    p = db_services.get_player(1)
    assert p is None

def test_get_all_players(cursor_mock):
    cursor_mock.fetchall.return_value = [(1, "erlend", 1000)]
    players = db_services.get_all_players()
    cursor_mock.fetchall.assert_called_once()
    assert players[0].get_id() == 1
    assert players[0].get_rating() == 1000
    assert players[0].get_name() == "erlend"

def test_delete_match(cursor_mock):
    db_services.delete_match(1)
    cursor_mock.execute.assert_called_once()

def test_get_matches(cursor_mock):
    cursor_mock.fetchall.return_value = [(5, 2, 3, 11, 0, 1000, 1000),
                                         (4, 2, 3, 11, 0, 1000, 1000),
                                         (3, 2, 3, 11, 0, 1000, 1000),
                                         (2, 2, 3, 11, 0, 1000, 1000),
                                         (1, 2, 3, 11, 0, 1000, 1000)]
    res = db_services.get_matches(1)
    assert res == [{'id': 5, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000}]
    res = db_services.get_matches(5)
    assert res == [{'id': 5, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000},
                   {'id': 4, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000},
                   {'id': 3, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000},
                   {'id': 2, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000},
                   {'id': 1, 'winner_id': 2, 'score': '11-0', 'loser_id': 3, 'winner_rating': 1000, 'loser_rating': 1000}]

def test_update_player(cursor_mock):
    cursor_mock.fetchall.return_value = [("bla", "Ola")]
    res = db_services.update_player_name(Player(1, "bla", 1000), "erlend")
    assert res
    assert cursor_mock.execute.call_count == 3

def test_update_player_name_exists(cursor_mock):
    cursor_mock.fetchall.return_value = [("Erlend","Ola")]
    res = db_services.update_player_name(Player(1, "bla", 1000), "erlend")
    assert not res
    cursor_mock.execute.assert_called_once()


def test_update_player_rating(cursor_mock):
    p = Player(1, "erlend", 1000)
    res = db_services.update_player_rating(p, 1001)
    calls = [mock.call("UPDATE Player SET rating = {} WHERE id = '{}';".format(1001, 1))]
    cursor_mock.execute.assert_has_calls(calls)
    assert cursor_mock.execute.call_count == 1
    assert res

