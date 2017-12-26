import re
import time
import pingpong.db_services as db_services
import pingpong.slack_services as slack_services

from pingpong.Player import Player

# starterbot's user ID in Slack: value is assigned after the bot starts up
pingpongbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+)>(.*)"
COMMAND_REGEX = "([a-zA-Z]*)( .*)?"
COMMAND_TYPES = ['name', 'help', 'match', 'stats']

EXAMPLE_COMMAND = "help"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        print(event)
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
        response = init_player(sender_id, channel)
    elif command_type == None or command_type not in COMMAND_TYPES:
        response = 'Not sure what you mean. Try *{}*.'.format(EXAMPLE_COMMAND)
    elif command_type == 'help':
        response = 'Here is some help.'
    elif command_type == 'name':
        response = set_name(player, command_value)
    elif command_type == 'match':
        response = add_match(command_value)
    elif command_type == 'stats':
        response = get_stats(command_value)

    slack_services.send_message(response, channel)

def init_player(sender_id):
    player = Player(sender_id, 'NoName')
    db_services.add_player(player)
    return "Hi, you seem to be a new player. I've registered you in my system, but I dont have a name for you yet. " \
           "Please set your name by typing *name* <yourname>."

def set_name(player, name):
    success = db_services.update_player_name(player, name)
    if success:
        return "Okay, {}. I've updated your name.".format(name)
    return "That name already exists. Please choose another one."

def add_match(match_string):
    match_regex = '(.*) (.*) (\d*)[ |-](\d*)'
    parsed_match_string = re.match(match_regex, match_string)
    if parsed_match_string:
        player1_name, player2_name, score1, score2 = parsed_match_string.group(1), parsed_match_string.group(2), \
                                                   parsed_match_string.group(3), parsed_match_string.group(4)
        db_services.add_match_result(player1_name, player2_name, score1, score2)
        return "Okay, I added the result :)"
    return "That's not how you add a new match result. Type *match* <playername> <playername> <points> <points>."

def get_stats(name):
    if name:
        response = get_player_stats(name)
    else:
        total_matches, scoreboard = db_services.get_stats()
        printable_scoreboard = format_scoreboard(scoreboard)
        response = "Total Matches played: {}\n" \
                   "{}".format(total_matches, printable_scoreboard)
    return response

def get_player_stats(name):
    player_stats = db_services.get_player_stats(name)
    response = "Here are the stats for {}.".format(name)

def format_scoreboard(scoreboard):
    s = ("{:^15}|" * len(scoreboard.keys())) + " {:20}".format('') + "\n"
    s = s.format(*([s[0] for s in list(scoreboard.keys())]))
    for row in scoreboard:
        s_row = ("{:^15}|" * len(scoreboard.items())) + " {:20}".format(row)  + "\n"
        s_row = s_row.format(*([i[1] if row != i[0] else 'x' for i in list(scoreboard[row].items())]))
        s += s_row
    print(s)
    return s


if __name__ == "__main__":
    if slack_services.slack_client.rtm_connect(with_team_state=False):
        print ("Ping Pong Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        pingpongbot_id = slack_services.slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_services.slack_client.rtm_read())
            if command:
                handle_command(command, channel, sender)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")