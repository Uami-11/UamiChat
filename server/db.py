import os

from . import models
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


def get_password_hash(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def create_user(username: str, hashed_password: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, is_online",
        (
            username,
            hashed_password,
        ),
    )

    conn.commit()
    row = cur.fetchone()
    conn.close()

    if row:
        return models.User(
            id=row["id"], username=row["username"], is_online=row["is_online"]
        )


def get_user_by_id(id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE id=%s", (id,))

    row = cur.fetchone()
    conn.close()

    if row:
        return models.User(id=id, username=row["username"], is_online=row["is_online"])
    return None


def set_user_online(user_id, status: bool):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "UPDATE users SET is_online=%s WHERE id=%s",
        (
            status,
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def save_message(sender_id, message, room_id=None, recipient_id=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "INSERT INTO messages (sender_id, message, room_id, recipient_id) VALUES (%s, %s, %s, %s) RETURNING message",
        (sender_id, message, room_id, recipient_id),
    )

    conn.commit()

    row = cur.fetchone()
    conn.close()
    if row:
        return row["message"]


def get_unread_dms(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT m.sender_id, m.message FROM messages m WHERE m.is_read = FALSE AND m.recipient_id = %s",
        (user_id,),
    )

    unread_list = cur.fetchall()
    conn.close()

    return unread_list


def mark_message_read(user_id, sender_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "UPDATE messages m SET m.is_read = TRUE WHERE m.recipient_id = %s AND m.sender_id = %s",
        (
            user_id,
            sender_id,
        ),
    )
    conn.commit()
    conn.close()
