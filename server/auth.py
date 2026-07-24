import hashlib

import db


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    user = db.get_user_by_username(username)
    if user:
        return {
            "success": False,
            "message": "username is already taken",
        }
    hashed_password = hash_password(password)

    user = db.create_user(username, hashed_password)

    return {"success": True if user else False, "user": user}
