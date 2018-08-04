import re
import time

from services import db_services
from services import slack_services
from models.Player import Player

# starterbot's user ID in Slack: value is assigned after the bot starts up
pingpongbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@([A-Z0-9]{9})>(.*)"
COMMAND_REGEX = "([a-zA-Z]*)( .*)?"
COMMAND_TYPES = ['name', 'help', 'match', 'stats', 'undo']

EXAMPLE_COMMAND = "help"

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

    player = db_services.get_player(sender_id)
    parsed_command = re.match(COMMAND_REGEX, command)
    command_type, command_value = None, None
    if parsed_command:
        command_type = parsed_command.group(1)
        if parsed_command.group(2):
            command_value = parsed_command.group(2).strip()

    if player == None:
        response = init_player(sender_id)
    elif command_type == None or command_type not in COMMAND_TYPES:
        response = 'Not sure what you mean. Try *{}*.'.format(EXAMPLE_COMMAND)
    elif command_type == 'help':
        response = help()
    elif command_type == 'name':
        if command_value:
            response = set_name(player, command_value.lower())
        else:
            response = "Your name is {}.".format(player.get_name())
    elif command_type == 'match':
        response = add_match(command_value)
    elif command_type == 'stats':
        response = get_stats(command_value)
    elif command_type == 'undo':
        response = undo_last_match()

    slack_services.send_message(response, channel)

def init_player(sender_id):
    player = Player(sender_id, sender_id, 1000)
    db_services.add_player(player)
    return "Hi, you seem to be a new player. I've registered you in my system, but I dont have a name for you yet. " \
           "Please set your name by typing *name* <yourname>."

def set_name(player, name):
    success = db_services.update_player_name(player, name)
    if success:
        return "Okay, {}. I've updated your name.".format(name)
    return "That name already exists. Please choose another one."

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
        new_ratings = db_services.add_match_result(player1_id, nondom1 == 'nd', player2_id, nondom2 == 'nd', score1, score2)
        player1_name = db_services.get_player(player1_id).get_name()
        player2_name = db_services.get_player(player2_id).get_name()
        if new_ratings[0]:
            return "Okay, I added the result! Your new ratings are:\n" \
                   "{}: {} ({})\n" \
                   "{}: {} ({})\n"\
                .format(player1_name + ('(nd)' if nondom1 == 'nd' else ''), new_ratings[0], ('+' if new_ratings[2] >= 0 else '') + str(new_ratings[2]),
                        player2_name + ('(nd)' if nondom2 == 'nd' else ''), new_ratings[1], ('+' if new_ratings[3] >= 0 else '') + str(new_ratings[3]))
        return "Hm. There seems to be something wrong with your input."
    return "That's not how you add a new match result. Type *match* @<name> @<name> <points> <points>."

def undo_last_match():
    latest_match = db_services.get_matches(limit=1)[0]
    loser_id = latest_match.get("loser_id")
    winner_id = latest_match.get("winner_id")
    loser_rating = latest_match.get("loser_rating")
    winner_rating = latest_match.get("winner_rating")
    loser_name = db_services.get_player(loser_id).get_name()
    winner_name = db_services.get_player(winner_id).get_name()

    db_services.delete_match(latest_match.get("id"))
    db_services.update_player_rating(Player(loser_id, "whatever", loser_rating), loser_rating)
    db_services.update_player_rating(Player(winner_id, "whatever", winner_rating), winner_rating)

    return "OK, I've undone the last match. Your new ratings are:\n" \
                   "{}: {}\n" \
                   "{}: {}\n"\
        .format(winner_name, winner_rating, loser_name, loser_rating)


def get_stats(name):
    leaderboard = db_services.get_leaderboard()
    if name:
        response = get_player_stats(name.lower(), leaderboard)
    else:
        total_matches, _ = db_services.get_stats()
        printable_leaderboard = format_leaderboard(leaderboard)
        response = "Total Matches played: {}\n" \
                   "{}".format(total_matches, printable_leaderboard)
    return response

def get_player_stats(name, leaderboard):
    wins, losses, rating, ratio = 0, 0, 0, 0
    for l in leaderboard:
        if l['Name'] == name:
            wins = l['Wins']
            losses = l['Losses']
            rating = l['Rating']
            ratio = l['W/L Ratio']
    response = "Here are the stats for {}:\nRating: {:.2f}\nW/L Ratio: {}\nWins: {}\nLosses: {}"\
        .format(name, rating, ratio, wins, losses)
    response += "\n\nFor more stats go to https://pingpong-cognite.herokuapp.com/"
    return response

def format_leaderboard(leaderboard):
    s = ''
    for i, l in enumerate(leaderboard):
        s += '{}. {} ({})\n'.format(i + 1, l['Name'], l['Rating'])
    s += "\nFor more detailed stats go to https://pingpong-cognite.herokuapp.com/"
    return s

def help():
    s = '*match @<name> @<name> <points> <points>*: Add a new match result.\n' \
        '*name*: Get your display name.\n' \
        '*name <newname>*: Update your display name.\n' \
        '*stats*: Get ping pong statistics.\n' \
        '*stats <name>*: Get stats for a specific player.\n' \
        '*undo*: Undo the last match registered.\n\n' \
        'Add a nondominant-hand modifier (nd) behind a name in a *match* command to signalize that a nondominant hand was used\n' \
        'Example: *match @erlend.vollset @ola.liabotro 11 0*\n\n' \
        'To see the Cognite Ping Pong Leaderboard go to https://pingpong-cognite.herokuapp.com/'
    return s

if __name__ == "__main__":
    if slack_services.slack_client.rtm_connect(with_team_state=False):
        print ("Ping Pong Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        pingpongbot_id = slack_services.slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_services.slack_client.rtm_read())
            if command and channel == "D8J3CN9DX":
                handle_command(command, channel, sender)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")