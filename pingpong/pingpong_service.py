from typing import Tuple

from pingpong.models import Player, Match
from pingpong.cdf_backend import CDFBackend
from pingpong.constants import DOMINANT, NON_DOMINANT

CDF_BACKEND = CDFBackend()

def add_new_player(id):
    player = Player(id, id)
    CDF_BACKEND.create_player(player)


def get_player(player_id):
    players = CDF_BACKEND.get_players(ids=[player_id])
    if players:
        return players[0]
    raise PlayerDoesNotExist()


def update_display_name(player, new_name):
    players = CDF_BACKEND.get_players()
    names = [p.get_name().lower() for p in players]
    if new_name.lower() in names:
        return False
    CDF_BACKEND.update_player(player.get_id(), new_name=new_name)
    return True


def add_match(p1_id: str, nd1: bool, p2_id: str, nd2: bool, score_p1: int, score_p2: int) -> Tuple[Player, int, Player, int]:
    if p1_id == p2_id or int(score_p1) == int(score_p2):
        raise InvalidMatchRegistration()

    p1_hand = NON_DOMINANT if nd1 else DOMINANT
    p2_hand = NON_DOMINANT if nd2 else DOMINANT
    p1 = get_player(p1_id)
    p2 = get_player(p2_id)

    if p1 and p2:
        match = Match(
            p1_id, p2_id, score_p1, score_p2, p1.get_rating(), p2.get_rating(), player1_hand=p1_hand, player2_hand=p2_hand
        )
        CDF_BACKEND.create_match(match)

        new_rating1, new_rating2 = calculate_new_elo_ratings(
            rating1=p1.get_rating(hand=p1_hand),
            rating2=p2.get_rating(hand=p2_hand),
            player1_win=int(match.player1_score) > int(match.player2_score)
        )
        CDF_BACKEND.update_player(p1.id, new_rating=new_rating1, hand=p1_hand)
        CDF_BACKEND.update_player(p2.id, new_rating=new_rating2, hand=p2_hand)

        new_p1 = get_player(p1.id)
        new_p2 = get_player(p2.id)

        updated_players = (new_p1, new_rating1 - p1.get_rating(), new_p2, new_rating2 - p2.get_rating())
        return updated_players
    raise PlayerDoesNotExist()

def undo_last_match():
    matches = CDF_BACKEND.get_matches()

    if not matches or True: #Todo: fix undo
        return None, None, None, None

    latest_match = matches[0]

    if latest_match.player1_score > latest_match.player2_score:
        winner = get_player(player_id=latest_match.player1_id)
        winner_prev_rating = latest_match.player1_rating
        loser = get_player(player_id=latest_match.player2_id)
        loser_prev_rating = latest_match.player2_rating
    else:
        winner = get_player(player_id=latest_match.player2_id)
        winner_prev_rating = latest_match.player2_rating
        loser = get_player(player_id=latest_match.player1_id)
        loser_prev_rating = latest_match.player1_rating


    CDF_BACKEND.delete_matches(ids=[latest_match.id])
    CDF_BACKEND.update_player(winner.id, new_rating=winner_prev_rating)
    CDF_BACKEND.update_player(loser.id, new_rating=loser_prev_rating)
    return winner.name, winner_prev_rating, loser.name, loser_prev_rating

def get_leaderboard():
    players = CDF_BACKEND.get_players()
    matches = CDF_BACKEND.get_matches()
    active_players = [p for p in players if __has_played_match(matches, p)]
    active_players = sorted(active_players, key=lambda p: p.get_rating(), reverse=True)
    printable_leaderboard = "\n".join(["{}. {} ({})".format(i + 1, p.get_name(), p.get_rating()) for i, p in enumerate(active_players)])
    return printable_leaderboard

def __has_played_match(matches, player):
    for match in matches:
        if match.player1_id == player.get_id() or match.player2_id == player.get_id():
            return True
    return False

def get_total_matches():
    matches = CDF_BACKEND.get_matches()
    return len(matches)

def get_player_stats(name):
    players = CDF_BACKEND.get_players()
    try:
        player = next(player for player in players if player.name == name)
    except StopIteration:
        raise PlayerDoesNotExist()
    wins = 0
    losses = 0
    matches = CDF_BACKEND.get_matches()
    for match in matches:
        if match.player1_id == player.id:
            if match.player1_score > match.player2_score:
                wins += 1
            else:
                losses += 1
        elif match.player2_id == player.id:
            if match.player2_score > match.player1_score:
                wins += 1
            else:
                losses += 1
    wl_ratio = "{:.2f}".format(wins/losses) if losses > 0 else '∞'
    return player.get_rating(), wins, losses, wl_ratio

def calculate_new_elo_ratings(rating1, rating2, player1_win):
    t1 = 10 ** (rating1 / 400)
    t2 = 10 ** (rating2 / 400)
    e1 = (t1 / (t1 + t2))
    e2 = (t2 / (t1 + t2))
    s1 = 1 if player1_win else 0
    s2 = 0 if player1_win else 1
    new_rating1 = rating1 + int(round(32 * (s1 - e1)))
    new_rating2 = rating2 + int(round(32 * (s2 - e2)))
    return new_rating1, new_rating2



class PlayerDoesNotExist(Exception):
    pass

class InvalidMatchRegistration(Exception):
    pass
