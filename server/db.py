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

def create_room(name, is_private, owner_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO rooms (room_name, is_private, owner_id)
            VALUES (%s, %s, %s)
            RETURNING id, room_name, is_private, owner_id
            """,
            (name, is_private, owner_id),
        )

        conn.commit()

        row = cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        row = None

    conn.close()

    if row:
        return models.Room(
            id=row["id"],
            room_name=row["room_name"],
            is_private=row["is_private"],
            owner_id=row["owner_id"],
        )

    return None


def get_room_by_name(name):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM rooms WHERE room_name = %s",
        (name,),
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return models.Room(
            id=row["id"],
            room_name=row["room_name"],
            is_private=row["is_private"],
            owner_id=row["owner_id"],
        )

    return None


def get_public_rooms():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM rooms WHERE is_private = FALSE"
    )

    rows = cur.fetchall()
    conn.close()

    rooms = []

    for row in rows:
        rooms.append(
            models.Room(
                id=row["id"],
                room_name=row["room_name"],
                is_private=row["is_private"],
                owner_id=row["owner_id"],
            )
        )

    return rooms


def add_room_member(room_id, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO room_members (room_id, user_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (room_id, user_id),
    )

    conn.commit()
    conn.close()


def get_room_members(room_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT u.*
        FROM users u
        JOIN room_members rm
        ON u.id = rm.user_id
        WHERE rm.room_id = %s
        """,
        (room_id,),
    )

    rows = cur.fetchall()
    conn.close()

    members = []

    for row in rows:
        members.append(
            models.User(
                id=row["id"],
                username=row["username"],
                is_online=row["is_online"],
            )
        )

    return members


def is_room_member(room_id, user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM room_members
        WHERE room_id = %s AND user_id = %s
        """,
        (room_id, user_id),
    )

    count = cur.fetchone()[0]
    conn.close()

    return count > 0


def send_friend_request(user_id, friend_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO friendships (user_id, friend_id, status)
        VALUES (%s, %s, 'pending')
        ON CONFLICT DO NOTHING
        """,
        (user_id, friend_id),
    )

    conn.commit()
    conn.close()


def accept_friend_request(user_id, friend_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE friendships
        SET status = 'accepted'
        WHERE user_id = %s AND friend_id = %s AND status = 'pending'
        """,
        (friend_id, user_id),
    )

    conn.commit()
    conn.close()


def decline_friend_request(user_id, friend_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM friendships
        WHERE user_id = %s AND friend_id = %s AND status = 'pending'
        """,
        (friend_id, user_id),
    )

    conn.commit()
    conn.close()


def get_friends(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT u.*
        FROM users u
        JOIN friendships f ON f.friend_id = u.id
        WHERE f.user_id = %s AND f.status = 'accepted'
        UNION
        SELECT u.*
        FROM users u
        JOIN friendships f ON f.user_id = u.id
        WHERE f.friend_id = %s AND f.status = 'accepted'
        """,
        (user_id, user_id),
    )

    rows = cur.fetchall()
    conn.close()

    friends = []

    for row in rows:
        friends.append(
            models.User(
                id=row["id"],
                username=row["username"],
                is_online=row["is_online"],
            )
        )

    return friends


def get_online_friends(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT u.*
        FROM users u
        JOIN friendships f ON f.friend_id = u.id
        WHERE f.user_id = %s AND f.status = 'accepted' AND u.is_online = TRUE
        UNION
        SELECT u.*
        FROM users u
        JOIN friendships f ON f.user_id = u.id
        WHERE f.friend_id = %s AND f.status = 'accepted' AND u.is_online = TRUE
        """,
        (user_id, user_id),
    )

    rows = cur.fetchall()
    conn.close()

    friends = []

    for row in rows:
        friends.append(
            models.User(
                id=row["id"],
                username=row["username"],
                is_online=row["is_online"],
            )
        )

    return friends


def block_user(user_id, target_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE friendships
        SET status = 'blocked'
        WHERE user_id = %s AND friend_id = %s
        """,
        (user_id, target_id),
    )

    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO friendships (user_id, friend_id, status)
            VALUES (%s, %s, 'blocked')
            """,
            (user_id, target_id),
        )

    conn.commit()
    conn.close()


def is_blocked(sender_id, recipient_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM friendships
        WHERE status = 'blocked'
        AND (
            (user_id = %s AND friend_id = %s)
            OR (user_id = %s AND friend_id = %s)
        )
        """,
        (recipient_id, sender_id, sender_id, recipient_id),
    )

    count = cur.fetchone()[0]
    conn.close()

    return count > 0
