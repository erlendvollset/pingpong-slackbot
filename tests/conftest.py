import os
import sys

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(src_dir)

import pytest

os.environ["DATABASE_URL"] = "postgresql://localhost/pingpong"

import db


@pytest.fixture(autouse=True)
def db_setup():
    clear_db()
    yield
    clear_db()


def clear_db():
    conn, cursor = db.connect()
    cursor.execute("DELETE FROM match;")
    cursor.execute("DELETE FROM player;")
    conn.commit()
    conn.close()
