import os
import re
import time

import pingpong_service

from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))

# starterbot's user ID in Slack: value is assigned after the bot starts up
pingpongbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@([A-Z0-9]{9})>(.*)"
COMMAND_REGEX = "([a-zA-Z]*)( .*)?"
COMMAND_TYPES = ['name', 'help', 'match', 'stats', 'undo']

def send_slack_message(message, channel):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel or 'G8JKTFJ6Q',
        text=message
    )

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            print(event)
            user_id, message = parse_direct_mention(event["text"])
            sender = event['user']
            if user_id == pingpongbot_id:
                return message, event["channel"], sender
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, sender_id):
    """
        Executes bot command if the command is known
    """
    parsed_command = re.match(COMMAND_REGEX, command)
    command_type, command_value = None, None
    if parsed_command:
        command_type = parsed_command.group(1)
        if parsed_command.group(2):
            command_value = parsed_command.group(2).strip()

    player = pingpong_service.get_player(sender_id)
    if not player:
        pingpong_service.add_new_player(sender_id)
        response = "Hi, you seem to be a new player. I've registered you in my system, but I dont have a name for " \
                   "you yet. Please set your name by typing `@pingpong name <yourname>`."
    elif command_type == None or command_type not in COMMAND_TYPES:
        response = 'Not sure what you mean. Try *help*.'
    elif command_type == 'help':
        response = help()
    elif command_type == 'name':
        if command_value:
            success = pingpong_service.update_display_name(player, command_value.lower())
            if success:
                response = "Ok. Your name is now {}".format(command_value.lower())
            else:
                response = "Sorry. That name is taken."
        else:
            response = "Your name is {}.".format(player.get_name())
    elif command_type == 'match':
        response = add_match(command_value)
    elif command_type == 'stats':
        response = get_stats(command_value)
    elif command_type == 'undo':
        w_name, w_rating, l_name, l_rating = pingpong_service.undo_last_match()
        response = "OK, I've undone the last match. Your new ratings are:\n" \
        "{}: {}\n" \
        "{}: {}\n" \
            .format(w_name, w_rating, l_name, l_rating)
    send_slack_message(response, channel)

def add_match(match_string):
    match_regex = '^<@([A-Z0-9]{9})> ((?:nd )?)<@([A-Z0-9]{9})> ((?:nd )?)(\d+)[ |-](\d+)'
    parsed_match_string = re.match(match_regex, match_string)
    if parsed_match_string:
        player1_id, nondom1, player2_id, nondom2, score1, score2 = parsed_match_string.group(1), \
                                                                       parsed_match_string.group(2).strip(), \
                                                                       parsed_match_string.group(3), \
                                                                       parsed_match_string.group(4).strip(), \
                                                                       parsed_match_string.group(5), \
                                                                       parsed_match_string.group(6)
        updated_players = pingpong_service.add_match(player1_id, nondom1 == "nd", player2_id, nondom2 == "nd", score1, score2)
        if updated_players:
            p1 = updated_players[0]
            p1_rating_diff = updated_players[1]
            p2 = updated_players[2]
            p2_rating_diff = updated_players[3]
            return "Okay, I added the result! Your new ratings are:\n" \
                   "{}: {} ({})\n" \
                   "{}: {} ({})\n"\
                .format(p1.get_name(), p1.get_rating(), ('+' if p1_rating_diff >= 0 else '') + str(p1_rating_diff),
                        p2.get_name(), p2.get_rating(), ('+' if p2_rating_diff >= 0 else '') + str(p2_rating_diff))
        return "Hm. There seems to be something wrong with your input."
    return "That's not how you add a new match result. Type *match* @<name> @<name> <points> <points>."


def get_stats(name):
    if name:
        rating, wins, losses, ratio = get_player_stats(name)
        response = "Here are the stats for {}:\nRating: {:.2f}\nW/L Ratio: {}\nWins: {}\nLosses: {}" \
            .format(name, rating, ratio, wins, losses)
    else:
        response = "Total Matches played: {}\n" \
                   "{}".format(pingpong_service.get_total_matches(), pingpong_service.get_leaderboard())
    return response

def help():
    s = '*match @<name> @<name> <points> <points>*: Add a new match result.\n' \
        '*name*: Get your display name.\n' \
        '*name <newname>*: Update your display name.\n' \
        '*stats*: Get ping pong statistics.\n' \
        '*stats <name>*: Get stats for a specific player.\n' \
        '*undo*: Undo the last match registered.\n\n' \
        'Add a nondominant-hand modifier (nd) behind a name in a *match* command to signalize that a nondominant hand was used\n' \
        'Example: *match @erlend.vollset nd @ola.liabotro 11 0*'
    return s

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print ("Ping Pong Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        pingpongbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_client.rtm_read())
            if command and (channel == "C8MAMM6AC" or sender == 'U6N8D853P'):
                handle_command(command, channel, sender)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")