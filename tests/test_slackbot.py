import pytest

from pingpong import slackbot, responses, pingpong_service
from pingpong.models import Player
from pingpong.slackbot import BotCommand

pingpongbot_id = "U9FID819D"
test_user_id = "U6N8D853P"
test_channel = "D8J3CN9DX"


@pytest.fixture(autouse=True, scope="session")
def set_pingpongbotid():
    slackbot.PINGPONG_BOT_ID = pingpongbot_id
    yield
    slackbot.PINGPONG_BOT_ID = None


@pytest.fixture
def players():
    conn, cursor = db.connect()
    p1 = Player(test_user_id, "erlend", 1000)
    p2 = Player(pingpongbot_id, "pingpong", 1000)
    db.create_player(cursor, p1)
    db.create_player(cursor, p2)
    conn.commit()
    conn.close()
    yield p1, p2


def text_to_slack_event(text: str) -> dict:
    return {'type': 'message',
            'user': test_user_id,
            'client_msg_id': 'b219e0ef-ce45-4ef8-b933-0b380144d800',
            'suppress_notification': False,
            'text': text,
            'team': 'T3XCNGHJL',
            'source_team': 'T3XCNGHJL',
            'user_team': 'T3XCNGHJL',
            'channel': test_channel,
            'event_ts': '1633539483.001800',
            'ts': '1633539483.001800'}


@pytest.mark.parametrize("test_input, expected", [
    (
            text_to_slack_event(f"<@{pingpongbot_id}> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand("match <@KD839FK38> <@9FJ48GJF8> 11 0", test_channel, test_user_id),
    ),
    (
            text_to_slack_event(f"<@NOT_BOT_ID'> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            None,
    ),
])
def test_parse_bot_commands(test_input, expected):
    assert slackbot.parse_bot_command(test_input) == expected


def test_add_player():
    slackbot.handle_command("hello", test_user_id)
    res = slackbot.handle_command("name erlend", test_user_id)

    conn, cursor = db.connect()
    players = db.get_players(cursor)
    conn.close()
    assert res == responses.name_updated("erlend")
    assert len(players) == 2
    assert players[0].get_name() == "erlend"
    assert players[0].get_id() == test_user_id
    assert players[1].get_name() == "erlend(nd)"
    assert players[1].get_id() == test_user_id + "(nd)"


def test_get_display_name(players):
    res = slackbot.handle_command("name emil", test_user_id)

    conn, cursor = db.connect()
    players = db.get_players(cursor, ids=[test_user_id, test_user_id + "(nd)"])
    conn.close()
    p = players[0]
    p_nd = players[1]

    assert res == responses.name_updated("emil")
    assert p.get_id() == test_user_id
    assert p.get_name() == "emil"
    assert p_nd.get_name() == "emil(nd)"


def test_get_display_name_taken(players):
    res = slackbot.handle_command("name pingpong", test_user_id)

    conn, cursor = db.connect()
    players = db.get_players(cursor, ids=[test_user_id, test_user_id + "(nd)"])
    conn.close()
    p = players[0]
    p_nd = players[1]

    assert res == responses.name_taken()
    assert p.get_id() == test_user_id
    assert p.get_name() == "erlend"
    assert p_nd.get_name() == "erlend(nd)"


def test_add_match(players):
    slackbot.handle_command("match   <@{}>   <@{}>    nd    11   0".format(test_user_id, pingpongbot_id), test_user_id)
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    p1 = db.get_players(cursor, [test_user_id])[0]
    p2 = db.get_players(cursor, [pingpongbot_id + "(nd)"])[0]
    conn.close()
    assert len(matches) == 1
    assert matches[0].player1_score == 11
    assert matches[0].player2_score == 0
    assert matches[0].player2_id == pingpongbot_id + "(nd)"
    assert matches[0].player1_rating == 1000
    assert p1.get_rating() == 1016
    assert p2.get_rating() == 984


def test_add_match_non_existing_player(players):
    res = slackbot.handle_command("match <@{}> <@XXXXXXXXX> nd 11 0".format(test_user_id), test_user_id)
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    conn.close()

    assert res == responses.player_does_not_exist()
    assert len(matches) == 0


def test_get_stats(players):
    pingpong_service.add_match(test_user_id, False, pingpongbot_id, False, 11, 0)
    res = slackbot.handle_command("stats", test_user_id)
    lb = "1. erlend (1016)\n2. pingpong (984)"
    assert res == responses.stats(1, lb)


def test_get_stats_no_active_players(players):
    res = slackbot.handle_command("stats", test_user_id)

    assert res == responses.stats(0, "")


def test_get_player_stats(players):
    res = slackbot.handle_command("stats erlend", test_user_id)
    assert res == responses.player_stats("erlend", 1000, "∞", 0, 0)


def test_get_player_stats_non_existing_player(players):
    res = slackbot.handle_command("stats notAUser", test_user_id)
    assert res == responses.player_does_not_exist()


def test_undo(players):
    pingpong_service.add_match(test_user_id, False, pingpongbot_id, False, 11, 0)
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    winner = db.get_players(cursor, ids=[test_user_id])[0]
    assert len(matches) == 1
    assert winner.get_rating() == 1016

    res = slackbot.handle_command("undo", test_user_id)

    assert res == responses.match_undone("erlend", 1000, "pingpong", 1000)

    players = db.get_players(cursor)
    conn.close()
    for p in players:
        assert p.get_rating() == 1000

    assert pingpong_service.get_total_matches() == 0
