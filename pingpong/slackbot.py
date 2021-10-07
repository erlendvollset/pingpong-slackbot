import os
import re
import logging
from dataclasses import dataclass
from typing import Tuple, Optional

from pingpong import responses, pingpong_service

from slack_sdk.rtm_v2 import RTMClient

logging.basicConfig(level="INFO")
log = logging.getLogger(__name__)

rtm = RTMClient(token=os.environ["SLACK_BOT_TOKEN"])

PINGPONG_BOT_ID = None
PINGPONG_CHANNEL_ID = "C8MAMM6AC"
ADMIN_CHANNEL_ID = "C02H9J7BP97"

MATCH_REGEX = "^<@([A-Z0-9]{9})>\s+((?:nd\s+)?)<@([A-Z0-9]{9})>\s+((?:nd\s+)?)(\d+)(\s+|-)(\d+)"
MENTION_REGEX = "^<@([A-Z0-9]{9})>(.*)"
COMMAND_REGEX = "([a-zA-Z]*)(\s+.*)?"
COMMAND_TYPES = ["name", "help", "match", "stats", "undo"]

@dataclass
class BotCommand:
    command: str
    channel: str
    sender_id: str

def parse_bot_command(event: dict) -> Optional[BotCommand]:
    if event["type"] == "message" and "subtype" not in event:
        user_id, message = parse_direct_mention(event["text"])
        sender = event["user"]
        if user_id == PINGPONG_BOT_ID:
            return BotCommand(message, event["channel"], sender)
    return None


def parse_direct_mention(message_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(bot_command: BotCommand) -> str:
    """
        Executes bot command if the command is known
    """
    parsed_command = re.match(COMMAND_REGEX, bot_command.command)
    command_type, command_value = None, None
    if parsed_command:
        command_type = parsed_command.group(1)
        if parsed_command.group(2):
            command_value = parsed_command.group(2).strip()
    try:
        player = pingpong_service.get_player(bot_command.sender_id)
    except pingpong_service.PlayerDoesNotExist:
        pingpong_service.add_new_player(bot_command.sender_id)
        return responses.new_player()

    if command_type == "help":
        return responses.help()
    if command_type == "name":
        if command_value:
            success = pingpong_service.update_display_name(player, command_value.lower())
            if success:
                return responses.name_updated(command_value.lower())
            else:
                return responses.name_taken()
        else:
            return responses.name(player.get_name())
    if command_type == "match":
        return handle_match_command(command_value)
    if command_type == "stats":
        name = command_value
        if name:
            try:
                rating, wins, losses, ratio = pingpong_service.get_player_stats(name)
                return responses.player_stats(name, rating, ratio, wins, losses)
            except pingpong_service.PlayerDoesNotExist:
                return responses.player_does_not_exist()
        else:
            return responses.stats(pingpong_service.get_total_matches(), pingpong_service.get_leaderboard())
    if command_type == "undo":
        w_name, w_rating, l_name, l_rating = pingpong_service.undo_last_match()
        return responses.match_undone(w_name, w_rating, l_name, l_rating)

    return responses.unkown_command()


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
                player1_id, nondom1 == "nd", player2_id, nondom2 == "nd", int(score1), int(score2)
            )
            return responses.match_added(
                p1.get_name(),
                p1.get_rating(),
                ("+" if p1_rating_diff >= 0 else "") + str(p1_rating_diff),
                p2.get_name(),
                p2.get_rating(),
                ("+" if p2_rating_diff >= 0 else "") + str(p2_rating_diff),
                )
        except pingpong_service.PlayerDoesNotExist:
            return responses.player_does_not_exist()
        except pingpong_service.InvalidMatchRegistration:
            return responses.invalid_match_registration()
    return responses.invalid_match_command()


@rtm.on("message")
def handle(client: RTMClient, event: dict) -> None:
    bot_command = parse_bot_command(event)
    if bot_command and (bot_command.channel == PINGPONG_CHANNEL_ID or bot_command.channel == ADMIN_CHANNEL_ID):
        response = handle_command(bot_command)
        client.web_client.chat_postMessage(channel=bot_command.channel, text=response)


def main():
    global PINGPONG_BOT_ID
    log.info("Starting pingpong bot")
    info = rtm.web_client.rtm_connect()
    PINGPONG_BOT_ID = info["self"]["id"]
    rtm.start()

if __name__ == "__main__":
    main()