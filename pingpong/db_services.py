import os
import psycopg2
from collections import OrderedDict
from urllib import parse
from pingpong.Player import Player

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
    cursor.execute("INSERT INTO Player (id, name) VALUES ('{}', '{}');".format(player.get_id(), player.get_name()))
    conn.commit()
    conn.close()

def add_match_result(player1_name, player2_name, score1, score2):
    conn, cursor = connect()
    cursor.execute("SELECT id FROM Player where name = '{}'".format(player1_name))
    player1_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM Player where name = '{}'".format(player2_name))
    player2_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO Match (player1, player2, scoreplayer1, scoreplayer2) "
                   "VALUES ('{}', '{}', {}, {});".format(player1_id, player2_id, score1, score2))
    conn.commit()
    conn.close()

def get_player(id):
    conn, cursor = connect()
    cursor.execute("SELECT * FROM Player WHERE Id = '{}';".format(id))
    result = cursor.fetchone()
    print(result)
    if result == None:
        return result
    conn.close()
    return Player(id, result[1])

def get_all_players():
    conn, cursor = connect()
    cursor.execute("SELECT * FROM Player;")
    results = cursor.fetchall()
    conn.close()
    return [Player(result[0], result[1]) for result in results]


def get_stats():
    conn, cursor = connect()
    cursor.execute("SELECT p1.name, match.scoreplayer1, p2.name, match.scoreplayer2 from Match "
                   "LEFT JOIN (select * from player) as p1 on p1.id = match.player1 "
                   "LEFT JOIN (select * from player) as p2 on p2.id = match.player2;")
    matches = cursor.fetchall()

    total_matches = len(matches)

    names = sorted(list(set([n[0] for n in matches] + [n[2] for n in matches])))
    scoreboard = OrderedDict()

    for n1 in names:
        row = OrderedDict()
        for n2 in names:
            row.update({n2: 0})
        scoreboard.update({n1: row})


    for m in matches:
        print(m)
        if int(m[1]) > int(m[3]):
            scoreboard[m[0]][m[2]] += 1
        else:
            scoreboard[m[2]][m[0]] += 1

    return total_matches, scoreboard

def update_player_name(player, name):
    conn, cursor = connect()
    cursor.execute("SELECT name FROM Player;")
    names = [n[0].lower() for n in cursor.fetchall()]
    if name.lower() in names:
        return False
    cursor.execute("UPDATE Player SET name = '{}' WHERE id = '{}';".format(name, player.get_id()))
    conn.commit()
    conn.close()
    return True


