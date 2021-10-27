from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import structlog
from slack_sdk.rtm_v2 import RTMClient

from src.backend.data_classes import Hand, Sport
from src.backend.util import BaseEnum
from src.pingpong import pingpong_service, responses
from src.pingpong.pingpong_service import PingPongService

log = structlog.getLogger(__name__)

PLAYER_REGEX = "<@([A-Z0-9]+)>"
MATCH_REGEX = f"^{PLAYER_REGEX}\s+((?:nd\s+)?){PLAYER_REGEX}\s+((?:nd\s+)?)(\d+)(\s+|-)(\d+)"
MENTION_REGEX = f"^{PLAYER_REGEX}(.*)"
COMMAND_REGEX = "([a-zA-Z]*)(\s+.*)?"


class CommandType(BaseEnum):
    NAME = "name"
    HELP = "help"
    MATCH = "match"
    STATS = "stats"
    UNDO = "undo"


class KeyWord(Enum):
    NON_DOMINANT = "nd"


@dataclass
class BotCommand:
    channel: str
    sender_id: str
    command_type: Optional[CommandType]
    command_value: Optional[str]
    recipient_id: Optional[str]

    @classmethod
    def from_slack_event(cls, event: dict) -> BotCommand:
        channel = event["channel"]
        sender = event["user"]
        message_text = event["text"]
        recipient_id, message = cls._parse_text_as_direct_mention(message_text)
        command_type_str, command_value = cls._parse_message_as_command(message)
        return BotCommand(channel, sender, CommandType.of(command_type_str), command_value, recipient_id)

    @staticmethod
    def _parse_text_as_direct_mention(
        message_text: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
        """
        matches = re.search(MENTION_REGEX, message_text)
        # the first group contains the username, the second group contains the remaining message
        if matches:
            return matches.group(1), matches.group(2).strip()
        return None, None

    @staticmethod
    def _parse_message_as_command(
        message: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        if not message:
            return None, None
        parsed_command = re.match(COMMAND_REGEX, message)
        command_type, command_value = None, None
        if parsed_command:
            command_type = parsed_command.group(1)
            if parsed_command.group(2):
                command_value = parsed_command.group(2).strip()
        return command_type, command_value


class PingPongSlackBot:
    def __init__(self, ping_pong_service: PingPongService, rtm_client: RTMClient, answer_in_channels: set[str]):
        self.ping_pong_service = ping_pong_service
        self.rtm_client = rtm_client
        self.answer_in_channels = answer_in_channels

        info = self.rtm_client.web_client.rtm_connect()
        self.ping_pong_bot_id = info["self"]["id"]
        self.rtm_client.on("message")(lambda client, event: self._handle(client, event))

    def start(self) -> None:
        log.info("Starting pingpong bot")
        self.rtm_client.start()

    @staticmethod
    def _event_info_to_log(event: dict[str, Any]) -> dict[str, Any]:
        essential_keys = {"user", "text", "team", "source_team", "user_team", "channel", "event_ts", "ts"}
        return {key: event.get(key) for key in essential_keys}

    def _handle(self, client: RTMClient, event: dict) -> None:
        if event["type"] != "message":
            return
        log.info("Received slack event", **self._event_info_to_log(event))
        bot_command = BotCommand.from_slack_event(event)
        if bot_command.recipient_id != self.ping_pong_bot_id:
            return
        if bot_command.channel not in self.answer_in_channels:
            return

        response = self._handle_bot_command(bot_command)
        client.web_client.chat_postMessage(channel=bot_command.channel, text=response)

    def _handle_bot_command(self, bot_command: BotCommand) -> str:
        """
        Executes bot command if the command is known
        """
        try:
            player = self.ping_pong_service.get_player(bot_command.sender_id)
        except pingpong_service.PlayerDoesNotExist:
            self.ping_pong_service.add_new_player(bot_command.sender_id)
            return responses.new_player()

        if bot_command.command_type is None:
            return responses.unknown_command()
        elif bot_command.command_type == CommandType.HELP:
            return responses.help()
        elif bot_command.command_type == CommandType.NAME:
            if bot_command.command_value:
                success = self.ping_pong_service.update_display_name(player, bot_command.command_value.lower())
                if success:
                    return responses.name_updated(bot_command.command_value.lower())
                else:
                    return responses.name_taken()
            else:
                return responses.name(player.name)
        elif bot_command.command_type == CommandType.MATCH:
            return self._handle_match_command(bot_command.command_value)
        elif bot_command.command_type == CommandType.STATS:
            name = bot_command.command_value
            if name:
                try:
                    rating, wins, losses, ratio = self.ping_pong_service.get_player_stats(name)
                    return responses.player_stats(name, rating, ratio, wins, losses)
                except pingpong_service.PlayerDoesNotExist:
                    return responses.player_does_not_exist()
            else:
                return responses.stats(
                    self.ping_pong_service.get_total_matches(), self.ping_pong_service.get_leaderboard()
                )
        elif bot_command.command_type == CommandType.UNDO:
            return responses.unknown_command()
            # w_name, w_rating, l_name, l_rating = pingpong_service.undo_last_match()
            # return responses.match_undone(w_name, w_rating, l_name, l_rating)
        return responses.unknown_command()

    def _handle_match_command(self, match_string: Optional[str]) -> str:
        if match_string is None:
            return responses.invalid_match_command()
        parsed_match_string = re.match(MATCH_REGEX, match_string)
        if not parsed_match_string:
            return responses.invalid_match_command()
        player1_id, nondom1, player2_id, nondom2, score1, score2 = (
            parsed_match_string.group(1),
            parsed_match_string.group(2).strip(),
            parsed_match_string.group(3),
            parsed_match_string.group(4).strip(),
            parsed_match_string.group(5),
            parsed_match_string.group(7),
        )
        try:
            p1_hand = Hand.NON_DOMINANT if nondom1 == KeyWord.NON_DOMINANT.value else Hand.DOMINANT
            p2_hand = Hand.NON_DOMINANT if nondom2 == KeyWord.NON_DOMINANT.value else Hand.DOMINANT
            p1, p1_rating_diff, p2, p2_rating_diff = self.ping_pong_service.add_match(
                player1_id,
                p1_hand,
                player2_id,
                p2_hand,
                int(score1),
                int(score2),
            )
            return responses.match_added(
                p1.name,
                p1.ratings.get(p1_hand, Sport.PING_PONG),
                ("+" if p1_rating_diff >= 0 else "") + str(p1_rating_diff),
                p2.name,
                p2.ratings.get(p2_hand, Sport.PING_PONG),
                ("+" if p2_rating_diff >= 0 else "") + str(p2_rating_diff),
            )
        except pingpong_service.PlayerDoesNotExist:
            return responses.player_does_not_exist()
        except pingpong_service.InvalidMatchRegistration:
            return responses.invalid_match_registration()
