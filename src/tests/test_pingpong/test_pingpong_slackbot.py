import time
from typing import Any, Callable, Optional
from unittest.mock import MagicMock

import pytest
from slack_sdk.rtm_v2 import RTMClient

from src.backend.backend import Backend
from src.backend.backend_in_memory import BackendInMemory
from src.backend.data_classes import Hand, Match, Player, Sport
from src.backend.rating import Ratings
from src.pingpong import responses
from src.pingpong.pingpong_service import PingPongService
from src.pingpong.slackbot import BotCommand, CommandType, PingPongSlackBot

PINGPONG_BOT_ID = "TESTTESTB"
USER_ID = "TESTTESTU"
CHANNEL_ID = "TESTTESTC"


def text_to_slack_event(text: str) -> dict[str, Any]:
    return {
        "type": "message",
        "user": USER_ID,
        "client_msg_id": "b219e0ef-ce45-4ef8-b933-0b380144d800",
        "suppress_notification": False,
        "text": text,
        "team": "T3XCNGHJL",
        "source_team": "T3XCNGHJL",
        "user_team": "T3XCNGHJL",
        "channel": CHANNEL_ID,
        "event_ts": "1633539483.001800",
        "ts": "1633539483.001800",
    }


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            text_to_slack_event(f"<@{PINGPONG_BOT_ID}> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand(CHANNEL_ID, USER_ID, CommandType.MATCH, "<@KD839FK38> <@9FJ48GJF8> 11 0", PINGPONG_BOT_ID),
        ),
        (
            text_to_slack_event("<@OTHER1234> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand(CHANNEL_ID, USER_ID, CommandType.MATCH, "<@KD839FK38> <@9FJ48GJF8> 11 0", "OTHER1234"),
        ),
        (
            text_to_slack_event("<@OTHERLONGERID123> match <@KD839FK38> <@9FJ48GJF8> 11 0"),
            BotCommand(CHANNEL_ID, USER_ID, CommandType.MATCH, "<@KD839FK38> <@9FJ48GJF8> 11 0", "OTHERLONGERID123"),
        ),
        (
            text_to_slack_event(f"<@{PINGPONG_BOT_ID}> stats"),
            BotCommand(CHANNEL_ID, USER_ID, CommandType.STATS, None, PINGPONG_BOT_ID),
        ),
        (
            text_to_slack_event("nomention"),
            BotCommand(CHANNEL_ID, USER_ID, None, None, None),
        ),
        (
            text_to_slack_event(f"<@{PINGPONG_BOT_ID}> random-invalid-command"),
            BotCommand(CHANNEL_ID, USER_ID, None, None, PINGPONG_BOT_ID),
        ),
    ],
)
def test_bot_command_from_slack_event(test_input: dict, expected: BotCommand) -> None:
    bot_command = BotCommand.from_slack_event(test_input)
    assert bot_command == expected


@pytest.fixture
def backend() -> Backend:
    return BackendInMemory()


@pytest.fixture
def ping_pong_service(backend: Backend) -> PingPongService:
    return PingPongService(backend=backend)


class SlackUserEmulator:
    def __init__(self) -> None:
        web_client_mock = MagicMock()
        web_client_mock.chat_postMessage.side_effect = self._set_response
        rtm_client = MagicMock()
        rtm_client.web_client = web_client_mock

        self._rtm_client = rtm_client
        self._event_handler: Optional[Callable[[RTMClient, dict[str, Any]], None]] = None
        self._response: Optional[str] = None

    def set_event_handler(self, event_handler: Callable[[RTMClient, dict[str, Any]], None]) -> None:
        self._event_handler = event_handler

    def send_message(self, message: str) -> str:
        if self._event_handler is None:
            raise RuntimeError("event_handler not set on invoker")
        self._event_handler(client=self._rtm_client, event=text_to_slack_event(message))  # type: ignore
        while (res := self._get_response()) is None:
            time.sleep(0.05)
        return res

    def send_bot_direct_message(self, message: str) -> str:
        return self.send_message(f"<@{PINGPONG_BOT_ID}> {message}")

    def send_name_update_message(self, name: str) -> str:
        return self.send_bot_direct_message(f"name {name}")

    def send_stats_message(self, name: Optional[str] = None) -> str:
        message = "stats"
        if name:
            message += f" {name}"
        return self.send_bot_direct_message(message)

    def send_match_message(
        self, id1: str, id2: str, score1: int, score2: int, nd1: bool = False, nd2: bool = False
    ) -> str:
        p1 = f"<@{id1}>{' nd' if nd1 else ''}"
        p2 = f"<@{id2}>{' nd' if nd2 else ''}"
        print(f"match {p1} {p2} {score1} {score2}")
        return self.send_bot_direct_message(f"match {p1} {p2} {score1} {score2}")

    def send_undo_message(self) -> str:
        return self.send_bot_direct_message("undo")

    def _set_response(self, *, channel: str, text: str) -> None:
        self._response = text

    def _get_response(self) -> Optional[str]:
        return self._response


@pytest.fixture
def slack_user_emulator() -> SlackUserEmulator:
    return SlackUserEmulator()


@pytest.fixture
def rtm_client(slack_user_emulator: SlackUserEmulator) -> RTMClient:
    rtm = MagicMock(RTMClient)
    rtm.on.side_effect = lambda event_type: slack_user_emulator.set_event_handler
    web_client_mock = MagicMock()
    web_client_mock.rtm_connect = lambda: {"self": {"id": PINGPONG_BOT_ID}}
    rtm.web_client = web_client_mock
    return rtm


@pytest.fixture(autouse=True)
def ping_pong_slackbot(ping_pong_service: PingPongService, rtm_client: RTMClient) -> PingPongSlackBot:
    return PingPongSlackBot(ping_pong_service, rtm_client, {CHANNEL_ID})


@pytest.fixture
def created_players(backend: Backend) -> list[Player]:
    p1 = backend.create_player(Player(USER_ID, "erlend", Ratings()))
    p2 = backend.create_player(Player("TESTID123", "name2", Ratings()))
    p3 = backend.create_player(Player("TESTID456", "name3", Ratings()))
    return [p1, p2, p3]


class TestPingPongSlackbot:
    def test_add_player(
        self, ping_pong_slackbot: PingPongSlackBot, slack_user_emulator: SlackUserEmulator, backend: Backend
    ) -> None:
        assert len(backend.list_players()) == 0
        response = slack_user_emulator.send_bot_direct_message("hello")
        assert response == responses.new_player()
        assert len(backend.list_players()) == 1

    def test_update_name(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player], backend: Backend
    ) -> None:
        new_name = "erlendnew"
        response = slack_user_emulator.send_name_update_message(new_name)
        assert response == responses.name_updated(new_name)
        player = backend.get_player(USER_ID)
        assert player is not None
        assert player.name == "erlendnew"

    def test_update_name_exists(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player], backend: Backend
    ) -> None:
        response = slack_user_emulator.send_name_update_message(created_players[-1].name)
        assert response == responses.name_taken()
        player = backend.get_player(USER_ID)
        assert player is not None
        assert player.name == "erlend"

    def test_add_match(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player], backend: Backend
    ) -> None:
        p1 = created_players[0]
        p2 = created_players[-1]
        response = slack_user_emulator.send_match_message(p1.id, p2.id, 11, 0)
        print(response)
        assert isinstance(response, str) and len(response) > 0

        matches = backend.list_matches(Sport.PING_PONG)
        assert len(matches) == 1
        assert matches[0] == Match(
            p1.id,
            p2.id,
            11,
            0,
            p1.ratings.get(Hand.DOMINANT, Sport.PING_PONG),
            p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG),
            Sport.PING_PONG,
            Hand.DOMINANT,
            Hand.DOMINANT,
        )
        p1_after = backend.get_player(p1.id)
        p2_after = backend.get_player(p2.id)
        assert p1_after is not None
        assert p2_after is not None
        assert p1.ratings.get(Hand.DOMINANT, Sport.PING_PONG) < p1_after.ratings.get(Hand.DOMINANT, Sport.PING_PONG)
        assert p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG) > p2_after.ratings.get(Hand.DOMINANT, Sport.PING_PONG)

    def test_add_match_with_non_dominant(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player], backend: Backend
    ) -> None:
        p1 = created_players[0]
        p2 = created_players[-1]
        response = slack_user_emulator.send_match_message(p1.id, p2.id, 50, 100, nd1=True)
        assert isinstance(response, str) and len(response) > 0

        matches = backend.list_matches(Sport.PING_PONG)
        assert len(matches) == 1
        assert matches[0] == Match(
            p1.id,
            p2.id,
            50,
            100,
            p1.ratings.get(Hand.NON_DOMINANT, Sport.PING_PONG),
            p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG),
            Sport.PING_PONG,
            Hand.NON_DOMINANT,
            Hand.DOMINANT,
        )
        p1_after = backend.get_player(p1.id)
        p2_after = backend.get_player(p2.id)
        assert p1_after is not None
        assert p2_after is not None
        assert p1.ratings.get(Hand.NON_DOMINANT, Sport.PING_PONG) > p1_after.ratings.get(
            Hand.NON_DOMINANT, Sport.PING_PONG
        )
        assert p2.ratings.get(Hand.DOMINANT, Sport.PING_PONG) < p2_after.ratings.get(Hand.DOMINANT, Sport.PING_PONG)

    def test_add_match_player_does_not_exist(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player], backend: Backend
    ) -> None:
        p1 = created_players[0]
        response = slack_user_emulator.send_match_message(p1.id, "DONOTEXIS", 50, 100, nd1=True)
        assert response == responses.player_does_not_exist()

        matches = backend.list_matches(Sport.PING_PONG)
        assert len(matches) == 0
        p1_after = backend.get_player(p1.id)
        assert p1_after is not None
        assert p1.ratings.get(Hand.NON_DOMINANT, Sport.PING_PONG) == p1_after.ratings.get(
            Hand.NON_DOMINANT, Sport.PING_PONG
        )

    def test_get_stats_no_active_players(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]
    ) -> None:
        response = slack_user_emulator.send_stats_message()
        assert response == responses.stats(0, "")

    def test_get_stats(self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]) -> None:
        p1 = created_players[0]
        p2 = created_players[-1]
        slack_user_emulator.send_match_message(p1.id, p2.id, 50, 100)
        slack_user_emulator.send_match_message(p1.id, p2.id, 100, 50)
        response = slack_user_emulator.send_stats_message()
        assert response == responses.stats(
            2,
            "1.  erlend (1001)\n2.  name3 (999)",
        )

    def test_get_stats_with_non_dominant(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]
    ) -> None:
        p1 = created_players[0]
        p2 = created_players[-1]
        slack_user_emulator.send_match_message(p1.id, p2.id, 50, 100)
        slack_user_emulator.send_match_message(p1.id, p2.id, 100, 50, nd1=True, nd2=True)
        slack_user_emulator.send_match_message(p1.id, p2.id, 100, 50, nd1=True, nd2=True)
        response = slack_user_emulator.send_stats_message()
        assert response == responses.stats(
            3,
            """1.  erlend(nd) (1031)
2.  name3 (1016)
3.  erlend (984)
4.  name3(nd) (969)""",
        )

    def test_get_player_stats(self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]) -> None:
        p1 = created_players[0]
        p2 = created_players[-1]
        slack_user_emulator.send_match_message(p1.id, p2.id, 50, 100)
        slack_user_emulator.send_match_message(p1.id, p2.id, 100, 50)
        response = slack_user_emulator.send_stats_message("erlend")
        assert response == responses.player_stats("erlend", 1001, "1.00", 1, 1)

    def test_get_player_stats_non_existing_player(
        self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]
    ) -> None:
        response = slack_user_emulator.send_stats_message("nope")
        assert response == responses.player_does_not_exist()

    def test_undo(self, slack_user_emulator: SlackUserEmulator, created_players: list[Player]) -> None:
        response = slack_user_emulator.send_undo_message()
        assert response == responses.unknown_command()
        # pingpong_service.add_match(TEST_USER_ID, False, PINGPONG_BOT_ID, False, 11, 0)
        # conn, cursor = db.connect()
        # matches = db.get_matches(cursor)
        # winner = db.list_players(cursor, ids=[TEST_USER_ID])[0]
        # assert len(matches) == 1
        # assert winner.get_rating() == 1016
        #
        # res = slackbot.handle_command("undo", TEST_USER_ID)
        #
        # assert res == responses.match_undone("erlend", 1000, "pingpong", 1000)
        #
        # players = db.list_players(cursor)
        # conn.close()
        # for p in players:
        #     assert p.get_rating() == 1000
        #
        # assert pingpong_service.get_total_matches() == 0
