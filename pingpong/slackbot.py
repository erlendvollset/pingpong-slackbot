from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple

from slack_sdk.rtm_v2 import RTMClient

from pingpong import pingpong_service, responses

logging.basicConfig(level="INFO")
log = logging.getLogger(__name__)

rtm = RTMClient(token=os.environ["SLACK_BOT_TOKEN"])

PINGPONG_BOT_ID = ""
PINGPONG_CHANNEL_ID = "C8MAMM6AC"
ADMIN_CHANNEL_ID = "C02H9J7BP97"
ANSWER_IN_CHANNELS = {PINGPONG_CHANNEL_ID, ADMIN_CHANNEL_ID}

PLAYER_REGEX = "<@([A-Z0-9]{9})>"
MATCH_REGEX = f"^{PLAYER_REGEX}\s+((?:nd\s+)?){PLAYER_REGEX}\s+((?:nd\s+)?)(\d+)(\s+|-)(\d+)"
MENTION_REGEX = f"^{PLAYER_REGEX}(.*)"
COMMAND_REGEX = "([a-zA-Z]*)(\s+.*)?"
COMMAND_TYPES = ["name", "help", "match", "stats", "undo"]


@dataclass
class BotCommand:
    command_type: Optional[str]
    command_value: Optional[str]
    channel: str
    sender_id: str
    recipient_id: Optional[str]

    @classmethod
    def from_slack_event(cls, event: dict) -> BotCommand:
        channel = event["channel"]
        sender = event["user"]
        message_text = event["text"]
        recipient_id, message = cls._parse_text_as_direct_mention(message_text)
        command_type, command_value = cls._parse_message_as_command(message)
        return BotCommand(command_type, command_value, channel, sender, recipient_id)

    @staticmethod
    def _parse_text_as_direct_mention(
        message_text: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
        """
        matches = re.search(MENTION_REGEX, message_text)
        # the first group contains the username, the second group contains the remaining message
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    @staticmethod
    def _parse_message_as_command(
        message: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        if not message:
            return None, None
        parsed_command = re.match(COMMAND_REGEX, message)
        command_type, command_value = None, None
        if parsed_command:
            command_type = parsed_command.group(1)
            if parsed_command.group(2):
                command_value = parsed_command.group(2).strip()
        return command_type, command_value


def handle_match_command(match_string: str) -> str:
    parsed_match_string = re.match(MATCH_REGEX, match_string)
    if parsed_match_string:
        player1_id, nondom1, player2_id, nondom2, score1, score2 = (
            parsed_match_string.group(1),
            parsed_match_string.group(2).strip(),
            parsed_match_string.group(3),
            parsed_match_string.group(4).strip(),
            parsed_match_string.group(5),
            parsed_match_string.group(7),
        )
        try:
            p1, p1_rating_diff, p2, p2_rating_diff = pingpong_service.add_match(
                player1_id,
                nondom1 == "nd",
                player2_id,
                nondom2 == "nd",
                int(score1),
                int(score2),
            )
            return responses.match_added(
                p1.name,
                p1.get_rating(),
                ("+" if p1_rating_diff >= 0 else "") + str(p1_rating_diff),
                p2.name,
                p2.get_rating(),
                ("+" if p2_rating_diff >= 0 else "") + str(p2_rating_diff),
            )
        except pingpong_service.PlayerDoesNotExist:
            return responses.player_does_not_exist()
        except pingpong_service.InvalidMatchRegistration:
            return responses.invalid_match_registration()
    return responses.invalid_match_command()


def handle_command(bot_command: BotCommand) -> str:
    """
    Executes bot command if the command is known
    """
    try:
        player = pingpong_service.get_player(bot_command.sender_id)
    except pingpong_service.PlayerDoesNotExist:
        pingpong_service.add_new_player(bot_command.sender_id)
        return responses.new_player()

    if bot_command.command_type is None or bot_command.command_value is None:
        return responses.unkown_command()

    if bot_command.command_type == "help":
        return responses.help()
    if bot_command.command_type == "name":
        if bot_command.command_value:
            success = pingpong_service.update_display_name(player, bot_command.command_value.lower())
            if success:
                return responses.name_updated(bot_command.command_value.lower())
            else:
                return responses.name_taken()
        else:
            return responses.name(player.name)
    if bot_command.command_type == "match":
        return handle_match_command(bot_command.command_value)
    if bot_command.command_type == "stats":
        name = bot_command.command_value
        if name:
            try:
                rating, wins, losses, ratio = pingpong_service.get_player_stats(name)
                return responses.player_stats(name, rating, ratio, wins, losses)
            except pingpong_service.PlayerDoesNotExist:
                return responses.player_does_not_exist()
        else:
            return responses.stats(pingpong_service.get_total_matches(), pingpong_service.get_leaderboard())
    # if bot_command.command_type == "undo":
    #     w_name, w_rating, l_name, l_rating = pingpong_service.undo_last_match()
    #     return responses.match_undone(w_name, w_rating, l_name, l_rating)
    return responses.unkown_command()


@rtm.on("message")
def handle(client: RTMClient, event: dict) -> None:
    if event["type"] != "message":
        return

    bot_command = BotCommand.from_slack_event(event)
    if bot_command.recipient_id != PINGPONG_BOT_ID:
        return
    if bot_command.channel not in ANSWER_IN_CHANNELS:
        return

    response = handle_command(bot_command)
    client.web_client.chat_postMessage(channel=bot_command.channel, text=response)


def main() -> None:
    global PINGPONG_BOT_ID
    log.info("Starting pingpong bot")
    info = rtm.web_client.rtm_connect()
    PINGPONG_BOT_ID = info["self"]["id"]
    rtm.start()


if __name__ == "__main__":
    main()
