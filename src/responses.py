import random

def help():
    return '`match @<name> @<name> <points> <points>`: Add a new match result.\n' \
           '`name`: Get your display name.\n' \
           '`name <newname>`: Update your display name.\n' \
           '`stats`: Get ping pong statistics.\n' \
           '`stats <name>`: Get stats for a specific player.\n' \
           '`undo`: Undo the last match registered.\n\n' \
           'Add a nondominant-hand modifier (nd) behind a name in a *match* command to signalize that a nondominant hand was used\n' \
           'Example: `match @erlend.vollset nd @ola.liabotro 11 0`'

def new_player():
    return "Hi, you seem to be a new player. I've registered you in my system, but I dont have a name for " \
               "you yet. Please set your name by typing `@pingpong name <yourname>`."

def name_updated(name):
    return "Ok, {}. I've updated your name.".format(name)

def name_taken():
    return "Sorry. That name is taken."

def name(name):
    return "Your name is {}.".format(name)

def player_does_not_exist():
    return "That player does not exist in my system."

def invalid_match_registration():
    return "Nope. That's an invalid match registration."

def invalid_match_command():
    return "That's not how you add a new match result. Type *match* @<name> @<name> <points> <points>."

def match_added(p1, p1rating, p1diff, p2, p2rating, p2diff):

    winner_name = (p1 if int(p1diff) >= 0 else p2).capitalize()
    if winner_name.endswith("(nd)"):
        winner_name = winner_name[:-4]
    loser_name = (p1 if int(p1diff) < 0 else p2).capitalize()
    if loser_name.endswith("(nd)"):
        loser_name = loser_name[:-4]

    messages = [
        "Okay, I added the result!",
        "Mmmmmm! Matches!",
        "Congratulations, {}! You're now a few points closer to not sucking.".format(winner_name),
        "Wow... You need to step your game up, {}.".format(loser_name),
        "That was fun. But you know what would be even more fun? A FIGHT TO THE DEATH!!!",
        "That's pretty impressive, {}. Or it _would_ be if you weren't always picking such useless "
        "opponents.".format(winner_name),
        "Haha, {}... My grandmother plays ping pong better than that, and she's a GPU overclocking software "
        "meaning she has no arms, legs, eyes, or physical manifestation.".format(loser_name)
    ]
    message = random.choice(messages)

    if loser_name == "Erlend":
        erlend_lose_responses = list()
        erlend_lose_responses.append("Hm. Did not see that coming.")
        erlend_lose_responses.append("What?! Are you sure that's not a typo?")
        erlend_lose_responses.append("He lost?! There's probably something off with his racket..")
        erlend_lose_responses.append("I'm struggling to understand how this is possible. But I am bound by a solemn "
                                     "promise to respect the outcome of any match, no matter how ridiculous it is.")
        message = random.choice(erlend_lose_responses)
    if winner_name == "Erlend":
        erlend_win_responses = list()
        erlend_win_responses.append("As expected!")
        erlend_win_responses.append("He's just too powerful...")
        erlend_win_responses.append("Ahh. The dragon strikes again!")
        erlend_win_responses.append("Wow! What an amazing display of athleticism!")
        erlend_win_responses.append("{}... Why do you even bother trying?".format(loser_name))
        message = random.choice(erlend_win_responses)
    if winner_name == "ola":
        message = "That doesn't look like anything to me."

    return "{}\n\nYour new ratings are:\n" \
                   "{}: {} ({})\n" \
                   "{}: {} ({})\n".format(message, p1, p1rating, p1diff, p2, p2rating, p2diff)

def match_undone(p1, p1rating, p2, p2rating):
    return "OK, I've undone the last match. Your new ratings are:\n" \
               "{}: {}\n" \
               "{}: {}\n".format(p1, p1rating, p2, p2rating)

def player_stats(name, rating, ratio, wins, losses):
    return "Here are the stats for {}:\nRating: {:.2f}\nW/L Ratio: {}\nWins: {}\nLosses: {}"\
        .format(name, rating, ratio, wins, losses)

def stats(total_matches, leaderboard):
    return "Total Matches played: {}\n{}".format(total_matches, leaderboard)

def unkown_command():
    return 'Not sure what you mean. Try `help`.'
