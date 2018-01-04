import os
import psycopg2
from collections import OrderedDict
from urllib import parse
from pingpong.Player import Player
from pingpong.helpers import update_scoreboard, update_leaderboard, calculate_new_elo_ratings

parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])

def connect():
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

    return conn, conn.cursor()

def add_player(player):
    conn, cursor = connect()
    cursor.execute("INSERT INTO Player (id, name, rating) VALUES ('{}', '{}', {});"
                   .format(player.get_id(), player.get_name(), player.get_rating()))
    cursor.execute("INSERT INTO Player (id, name, rating) VALUES ('{}(nd)', '{}(nd)', {});"
                   .format(player.get_id(), player.get_name(), player.get_rating()))
    conn.commit()
    conn.close()

def add_match_result(player1_name, nondom1, player2_name, nondom2, points1, points2):
    conn, cursor = connect()
    new_ratings = (None, None, None, None)
    cursor.execute("SELECT id, rating, name FROM Player where name = '{}{}'".format(player1_name, '(nd)' if nondom1 else ''))
    player1 = cursor.fetchone()
    cursor.execute("SELECT id, rating, name FROM Player where name = '{}{}'".format(player2_name, '(nd)' if nondom2 else ''))
    player2 = cursor.fetchone()
    print(player1, player2)
    if player1 and player2 and int(points1) != int(points2):
        cursor.execute("INSERT INTO Match (player1, player2, scoreplayer1, scoreplayer2) "
                       "VALUES ('{}', '{}', {}, {});"
                       .format('{}'.format(player1[0]),
                               '{}'.format(player2[0]),
                               points1,
                               points2))
        new_score1, new_score2 = calculate_new_elo_ratings(rating1=player1[1], rating2=player2[1], player1_win=int(points1) > int(points2))
        cursor.execute("UPDATE Player SET rating = {} WHERE name = '{}'".format(new_score1, player1[2]))
        cursor.execute("UPDATE Player SET rating = {} WHERE name = '{}'".format(new_score2, player2[2]))
        new_ratings = (new_score1, new_score2, new_score1 - player1[1], new_score2 - player2[1])
    conn.commit()
    conn.close()
    return new_ratings


def get_player(id):
    conn, cursor = connect()
    cursor.execute("SELECT * FROM Player WHERE Id = '{}';".format(id))
    result = cursor.fetchone()
    print(result)
    if result == None:
        return result
    conn.close()
    return Player(id, result[1], result[2])

def get_all_players():
    conn, cursor = connect()
    cursor.execute("SELECT * FROM Player;")
    results = cursor.fetchall()
    conn.close()
    return [Player(result[0], result[1], result[2]) for result in results]

def get_matches(limit=5):
    conn, cursor = connect()
    cursor.execute("SELECT match.id, p1.name, p2.name, match.scoreplayer1, match.scoreplayer2 from Match "
                   "LEFT JOIN (select * from player) as p1 on p1.id = match.player1 "
                   "LEFT JOIN (select * from player) as p2 on p2.id = match.player2 "
                   "ORDER BY match.id DESC;")
    matches = cursor.fetchall()
    matches_formatted = []
    for m in matches:
        if m[3] > m[4]:
            matches_formatted.append({"winner": m[1], "score": "{}-{}".format(m[3], m[4]), "loser": m[2]})
        else:
            matches_formatted.append({"winner": m[2], "score": "{}-{}".format(m[4], m[3]), "loser": m[1]})
    return matches_formatted[:limit]


def get_stats():
    conn, cursor = connect()
    cursor.execute("SELECT p1.name, match.scoreplayer1, p2.name, match.scoreplayer2 from Match "
                   "LEFT JOIN (select * from player) as p1 on p1.id = match.player1 "
                   "LEFT JOIN (select * from player) as p2 on p2.id = match.player2;")
    matches = cursor.fetchall()

    total_matches = len(matches)

    names = sorted(list(set([n[0] for n in matches] + [n[2] for n in matches])))
    scoreboard = []

    for n1 in names:
        row = OrderedDict()
        row.update({'name': n1})
        for n2 in names:
            if n2 == n1:
                row.update({n2: 'x'})
            else:
                row.update({n2: 0})

        scoreboard.append(row)
    for m in matches:
        if int(m[1]) > int(m[3]):
            scoreboard = update_scoreboard(m[0], m[2], scoreboard)
        else:
            scoreboard = update_scoreboard(m[2], m[0], scoreboard)

    return total_matches, scoreboard

def get_leaderboard():
    conn, cursor = connect()
    cursor.execute("SELECT p1.name, p2.name, scoreplayer1, scoreplayer2 FROM match "
                   "LEFT JOIN (SELECT * FROM player) as p1 on p1.id = match.player1 "
                   "LEFT JOIN (SELECT * FROM player) as p2 on p2.id = match.player2;")
    matches = cursor.fetchall()
    cursor.execute("SELECT name, rating FROM player;")
    leaderboard = [{"Rating": m[1], "Name": m[0], "W/L Ratio": 0, "Wins": 0, "Losses": 0} for m in cursor.fetchall()]
    for m in matches:
        if m[2] > m[3]:
            leaderboard = update_leaderboard(m[0], m[1], leaderboard)
        else:
            leaderboard = update_leaderboard(m[1], m[0], leaderboard)
    for l in leaderboard:
        l['W/L Ratio'] = '{:.2f}'.format(l['Wins'] / l['Losses']) if l['Losses'] > 0 else '∞'
    leaderboard = sorted([l for l in leaderboard if l['Wins'] + l['Losses'] > 0], key=lambda x: (x['Rating'], x['Wins']), reverse=True)
    return leaderboard

def update_player_name(player, name):
    conn, cursor = connect()
    cursor.execute("SELECT name FROM Player;")
    names = [n[0].lower() for n in cursor.fetchall()]
    if name.lower() in names:
        return False
    cursor.execute("UPDATE Player SET name = '{}' WHERE id = '{}';".format(name, player.get_id()))
    cursor.execute("UPDATE Player SET name = '{}(nd)' WHERE id = '{}(nd)';".format(name, player.get_id()))
    conn.commit()
    conn.close()
    return True
