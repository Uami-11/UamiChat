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


def get_user_by_id(id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE id=%s", (id,))

    row = cur.fetchone()

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


def save_message(sender_id, message, room_id=None, recipient_id=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "INSERT INTO messages (sender_id, message, room_id, recipient_id) VALUES (%s, %s, %s, %s)",
        (sender_id, message, room_id, recipient_id),
    )

    row = cur.fetchone()
    if row:
        return row["message"]


def get_unread_dms(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT m.sender_id, m.message FROM users u JOIN messages m ON m.recipient_id = u.id WHERE m.is_read = FALSE AND u.id = %s",
        (user_id,),
    )

    unread_list = cur.fetchall()

    return unread_list


def mark_message_read(user_id, sender_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "UPDATE messages m JOIN users u ON m.recipient_id = u.id SET m.is_read = TRUE WHERE u.id = %s AND m.sender_id = %s",
        (
            user_id,
            sender_id,
        ),
    )
