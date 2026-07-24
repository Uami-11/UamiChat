import os

import models
import psycopg2
from psycopg2.extras import RealDictCursor  # makes queries act like dictionaries


def get_connection():
    return psycopg2.connect(os.environ["DB_URL"])


def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # this cursor executes queries

    cur.execute("SELECT * FROM users WHERE username=%s", (username,))

    row = cur.fetchone()  # Results from query

    conn.close()

    if row:
        return models.User(
            id=row["id"], username=row["username"], is_online=row["is_online"]
        )

    return None


def create_user(username, hashed_password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, is_online",
        (
            username,
            hashed_password,
        ),
    )

    row = cur.fetchone()

    if row:
        return models.User(
            id=row["id"], username=row["username"], is_online=row["is_online"]
        )

    return None
