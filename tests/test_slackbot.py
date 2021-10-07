import pytest

from pingpong import pingpong_service, responses, slackbot
from pingpong.models import Player
from pingpong.slackbot import BotCommand

PINGPONG_BOT_ID = "U9FID819D"
TEST_USER_ID = "U6N8D853P"
TEST_CHANNEL = "D8J3CN9DX"

db = None


@pytest.fixture(autouse=True, scope="session")
def set_pingpongbotid():
    slackbot.PINGPONG_BOT_ID = PINGPONG_BOT_ID
    yield
    slackbot.PINGPONG_BOT_ID = None


@pytest.fixture
def players():
    conn, cursor = db.connect()
    p1 = Player(TEST_USER_ID, "erlend", 1000)
    p2 = Player(PINGPONG_BOT_ID, "pingpong", 1000)
    db.create_player(cursor, p1)
    db.create_player(cursor, p2)
    conn.commit()
    conn.close()
    yield p1, p2


def text_to_slack_event(text: str) -> dict:
    return {
        "type": "message",
        "user": TEST_USER_ID,
        "client_msg_id": "b219e0ef-ce45-4ef8-b933-0b380144d800",
        "suppress_notification": False,
        "text": text,
        "team": "T3XCNGHJL",
        "source_team": "T3XCNGHJL",
        "user_team": "T3XCNGHJL",
        "channel": TEST_CHANNEL,
        "event_ts": "1633539483.001800",
        "ts": "1633539483.001800",
    }


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            text_to_slack_event(f"<@{PINGPONG_BOT_ID}> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand(
                "match",
                "<@KD839FK38> <@9FJ48GJF8> 11 0",
                TEST_CHANNEL,
                TEST_USER_ID,
                PINGPONG_BOT_ID,
            ),
        ),
        (
            text_to_slack_event("<@NOT1BOTID> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand(
                "match",
                "<@KD839FK38> <@9FJ48GJF8> 11 0",
                TEST_CHANNEL,
                TEST_USER_ID,
                "NOT1BOTID",
            ),
        ),
    ],
)
def test_bot_command_from_slack_event(test_input, expected):
    assert slackbot.BotCommand.from_slack_event(test_input) == expected


def test_add_player():
    slackbot.handle_command("hello", TEST_USER_ID)
    res = slackbot.handle_command("name erlend", TEST_USER_ID)

    conn, cursor = db.connect()
    players = db.list_players(cursor)
    conn.close()
    assert res == responses.name_updated("erlend")
    assert len(players) == 2
    assert players[0].name == "erlend"
    assert players[0].id == TEST_USER_ID
    assert players[1].name == "erlend(nd)"
    assert players[1].id == TEST_USER_ID + "(nd)"


def test_get_display_name(players):
    res = slackbot.handle_command("name emil", TEST_USER_ID)

    conn, cursor = db.connect()
    players = db.list_players(cursor, ids=[TEST_USER_ID, TEST_USER_ID + "(nd)"])
    conn.close()
    p = players[0]
    p_nd = players[1]

    assert res == responses.name_updated("emil")
    assert p.id == TEST_USER_ID
    assert p.name == "emil"
    assert p_nd.name == "emil(nd)"


def test_get_display_name_taken(players):
    res = slackbot.handle_command("name pingpong", TEST_USER_ID)

    conn, cursor = db.connect()
    players = db.list_players(cursor, ids=[TEST_USER_ID, TEST_USER_ID + "(nd)"])
    conn.close()
    p = players[0]
    p_nd = players[1]

    assert res == responses.name_taken()
    assert p.id == TEST_USER_ID
    assert p.name == "erlend"
    assert p_nd.name == "erlend(nd)"


def test_add_match(players):
    slackbot.handle_command(
        "match   <@{}>   <@{}>    nd    11   0".format(TEST_USER_ID, PINGPONG_BOT_ID),
        TEST_USER_ID,
    )
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    p1 = db.list_players(cursor, [TEST_USER_ID])[0]
    p2 = db.list_players(cursor, [PINGPONG_BOT_ID + "(nd)"])[0]
    conn.close()
    assert len(matches) == 1
    assert matches[0].player1_score == 11
    assert matches[0].player2_score == 0
    assert matches[0].player2_id == PINGPONG_BOT_ID + "(nd)"
    assert matches[0].player1_rating == 1000
    assert p1.get_rating() == 1016
    assert p2.get_rating() == 984


def test_add_match_non_existing_player(players):
    res = slackbot.handle_command("match <@{}> <@XXXXXXXXX> nd 11 0".format(TEST_USER_ID), TEST_USER_ID)
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    conn.close()

    assert res == responses.player_does_not_exist()
    assert len(matches) == 0


def test_get_stats(players):
    pingpong_service.add_match(TEST_USER_ID, False, PINGPONG_BOT_ID, False, 11, 0)
    res = slackbot.handle_command("stats", TEST_USER_ID)
    lb = "1. erlend (1016)\n2. pingpong (984)"
    assert res == responses.stats(1, lb)


def test_get_stats_no_active_players(players):
    res = slackbot.handle_command("stats", TEST_USER_ID)

    assert res == responses.stats(0, "")


def test_get_player_stats(players):
    res = slackbot.handle_command("stats erlend", TEST_USER_ID)
    assert res == responses.player_stats("erlend", 1000, "∞", 0, 0)


def test_get_player_stats_non_existing_player(players):
    res = slackbot.handle_command("stats notAUser", TEST_USER_ID)
    assert res == responses.player_does_not_exist()


def test_undo(players):
    pingpong_service.add_match(TEST_USER_ID, False, PINGPONG_BOT_ID, False, 11, 0)
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    winner = db.list_players(cursor, ids=[TEST_USER_ID])[0]
    assert len(matches) == 1
    assert winner.get_rating() == 1016

    res = slackbot.handle_command("undo", TEST_USER_ID)

    assert res == responses.match_undone("erlend", 1000, "pingpong", 1000)

    players = db.list_players(cursor)
    conn.close()
    for p in players:
        assert p.get_rating() == 1000

    assert pingpong_service.get_total_matches() == 0
