from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    is_online: bool


@dataclass
class Room:
    id: int
    room_name: str
    is_private: bool
    owner_id: int


@dataclass
class Message:
    id: int
    sender_id: int
    room_id: int | None
    recipient_id: int | None
    message: str
    is_read: bool
    created_at: datetime
