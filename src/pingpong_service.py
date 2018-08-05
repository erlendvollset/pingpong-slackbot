import db
from models import Player, Match

def add_new_player(id):
    player = Player(id, id, 1000)
    conn, cursor = db.connect()
    db.create_player(cursor, player)
    conn.commit()
    conn.close()

def get_player(player_id):
    conn, cursor = db.connect()
    players = db.get_players(cursor, ids=[player_id])
    conn.close()
    if players:
        return players[0]
    return None

def update_display_name(player, new_name):
    conn, cursor = db.connect()
    players = db.get_players(cursor)
    names = [p.get_name().lower() for p in players]
    if new_name.lower() in names:
        return False
    db.update_player(cursor, player.get_id(), new_name=new_name)
    conn.commit()
    conn.close()
    return True

def add_match(p1_id, nd1, p2_id, nd2, score_p1, score_p2):
    if p1_id == p2_id or int(score_p1) == int(score_p2):
        return None

    p1_id += "(nd)" if nd1 else ""
    p1 = get_player(p1_id)
    p2_id += "(nd)" if nd2 else ""
    p2 = get_player(p2_id)

    if p1 and p2:
        match = Match(None, p1_id, p2_id, score_p1, score_p2, p1.get_rating(), p2.get_rating())
        conn, cursor = db.connect()
        db.create_match(cursor, match)

        new_rating1, new_rating2 = calculate_new_elo_ratings(rating1=p1.get_rating(), rating2=p2.get_rating(),
                                                                  player1_win=int(match.player1_score) > int(match.player2_score))
        db.update_player(cursor, p1.id, new_rating=new_rating1)
        db.update_player(cursor, p2.id, new_rating=new_rating2)
        conn.commit()
        conn.close()

        new_p1 = get_player(p1.id)
        new_p2 = get_player(p2.id)

        updated_players = (new_p1, new_rating1 - p1.get_rating(), new_p2, new_rating2 - p2.get_rating())
        return updated_players
    return None

def undo_last_match():
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)

    if not matches:
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


    db.delete_matches(cursor, ids=[latest_match.id])
    db.update_player(cursor, winner.id, new_rating=winner_prev_rating)
    db.update_player(cursor, loser.id, new_rating=loser_prev_rating)
    conn.commit()
    conn.close()
    return winner.name, winner_prev_rating, loser.name, loser_prev_rating

def get_leaderboard():
    conn, cursor = db.connect()
    players = db.get_players(cursor)
    conn.close()
    printable_leaderboard = "\n".join(["{}. {} ({})".format(i + 1, p.get_name(), p.get_rating()) for i, p in enumerate(players)])
    return printable_leaderboard

def get_total_matches():
    conn, cursor = db.connect()
    matches = db.get_matches(cursor)
    conn.close()
    return len(matches)

def get_player_stats(name):
    conn, cursor = db.connect()
    players = db.get_players(cursor)
    player = next(player for player in players if player.name == name)
    wins = 0
    losses = 0
    matches = db.get_matches(cursor)
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
    wl_ratio = str(wins/losses) if losses > 0 else '∞'
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



