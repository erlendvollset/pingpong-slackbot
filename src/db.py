import os

from typing import List
from urllib import parse
import psycopg2

from models import Player, Match
import util

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

def create_player(cursor, player: Player):
    cursor.execute("INSERT INTO Player (id, name, rating) VALUES ('{}', '{}', {});"
                   .format(player.get_id(), player.get_name(), player.get_rating()))
    cursor.execute("INSERT INTO Player (id, name, rating) VALUES ('{}(nd)', '{}(nd)', {});"
                   .format(player.get_id(), player.get_name(), player.get_rating()))

def get_players(cursor, ids: List[int] = None):
    if ids:
        cursor.execute("SELECT * from Player WHERE id in ({}) ORDER BY rating DESC;".format(", ".join(["'{}'".format(id) for id in ids])))
    else:
        cursor.execute("SELECT * from Player ORDER BY rating DESC;")
    res = cursor.fetchall()
    return [Player(*p) for p in res]

def delete_players(cursor, ids: List[int]):
    cursor.execute("DELETE FROM Player WHERE id in ({})".format(", ".join(["'{}'".format(id) for id in ids])))

def update_player(cursor, id: int, new_name=None, new_rating=None) -> bool:
    if new_name:
        cursor.execute("UPDATE Player SET name = '{}' WHERE id = '{}';".format(new_name, id))
        cursor.execute("UPDATE Player SET name = '{}(nd)' WHERE id = '{}(nd)';".format(new_name, id))
    if new_rating:
        cursor.execute("UPDATE Player SET rating = {} WHERE id = '{}';".format(new_rating, id))
    return True

def create_match(cursor, match: Match):
    cursor.execute("INSERT INTO Match (player1, player2, scoreplayer1, scoreplayer2, player1rating, player2rating) "
                   "VALUES ('{}', '{}', {}, {}, {}, {});"
                   .format('{}'.format(match.player1_id),
                           '{}'.format(match.player2_id),
                           match.player1_score,
                           match.player2_score,
                           match.player1_rating,
                           match.player2_rating))

def get_matches(cursor, ids: List[int] = None):
    if ids:
        cursor.execute("SELECT * from Match WHERE id in ({}) ORDER BY id DESC;".format(", ".join(["'{}'".format(id) for id in ids])))
    else:
        cursor.execute("SELECT * from Match ORDER BY id DESC;")
    res = cursor.fetchall()
    return [Match(*match) for match in res]

def delete_matches(cursor, ids: List[int]):
    cursor.execute("DELETE FROM Match WHERE id in ({})".format(", ".join(["'{}'".format(id) for id in ids])))

