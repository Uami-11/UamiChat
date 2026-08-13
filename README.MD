# UamiChat

A CLI-based real-time chat application inspired by IRC. Users connect to a self-hosted WebSocket server and communicate through their terminal using commands.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.14 |
| Real-time communication | `websockets` |
| Database | PostgreSQL via `psycopg2` |
| Terminal UI | `rich` |
| Dev environment | Docker + Docker Compose |

## Prerequisites

- Python 3.14
- Docker + Docker Compose
- Git
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Getting Started

```bash
# clone the repo
git clone https://github.com/Uami-11/UamiChat.git
cd UamiChat

# create and activate virtual environment
uv venv
source .venv/bin/activate

# install dependencies
uv pip install -r requirements.txt

# create your .env file
cp .env.example .env

# start Postgres + server
docker compose up --build

# in another terminal, test the connection
python client/test.py
```

You should see:
```
Connected to server
Ping response: {'type': 'pong'}
Register response: {'type': 'success', 'message': 'registered', 'username': 'testuser'}
Login response: {'type': 'success', 'message': 'logged in', 'username': 'testuser'}
Disconnected
```

To stop everything:
```bash
docker compose down
```

## Git Workflow

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Stable production code. Only merged via PR after review. |
| `dev` | Integration branch. All features merge here first. |
| `feature/<your-branch>` | Your personal working branch. |

### Daily Workflow

```bash
# start your day — pull latest dev into your branch
git checkout dev
git pull origin dev
git checkout feature/<your-branch>
git merge dev

# when you finish a piece of work
git add .
git commit -m "short description of what you did"
git push origin feature/<your-branch>

# then open a PR on GitHub: feature/<your-branch> → dev
# message the group so Nirwan can merge it
```

### Rules

1. **Never push directly to `dev` or `main`.** Always use a PR.
2. **Pull from `dev` every morning** before writing code. This gives you everyone else's merged work.
3. **When you finish a PR**, message the group so others know to pull dev into their branch before their next commit.
4. **Keep commits small and focused.** One feature or fix per commit.

---

## Project Structure

```
UamiChat/
├── server/
│   ├── __init__.py        makes server/ a Python package
│   ├── main.py            WebSocket server entry point
│   ├── db.py              all database queries
│   ├── auth.py            registration, login, password hashing
│   ├── handler.py         routes incoming messages to correct functions
│   └── models.py          dataclasses for User, Room, Message
├── client/
│   ├── connection.py      WebSocket wrapper (connect/send/receive/disconnect)
│   ├── commands.py        parses user input into command dicts
│   ├── ui.py              rich terminal rendering
│   ├── main.py            client entry point, auth flow, main loop
│   └── test.py            example client (replace with your own main.py)
├── sql/
│   └── schema.sql         all CREATE TABLE statements
├── Dockerfile             containerizes the server
├── docker-compose.yml     Postgres + server for local development
├── requirements.txt       Python dependencies
├── .env.example           environment variable template
└── docs/
    └── UamiChat-project.md  full project documentation
```

## Existing Code

These files are already built and working. **Do not edit them** unless instructed.

### `sql/schema.sql`

Five tables:
- `users` — id, username, password_hash, is_online, created_at
- `rooms` — id, room_name, is_private, owner_id, created_at
- `room_members` — room_id, user_id (composite primary key)
- `messages` — id, sender_id, room_id, recipient_id, message, is_read, created_at
- `friendships` — user_id, friend_id, status (composite primary key)

### `server/models.py`

Three dataclasses:
- `User(id, username, is_online)`
- `Room(id, room_name, is_private, owner_id)`
- `Message(id, sender_id, room_id, recipient_id, message, is_read, created_at)`

### `server/db.py`

Functions already built:
- `get_connection()` — opens a psycopg2 connection using DB_URL from environment
- `get_user_by_username(username)` — returns User or None
- `get_user_by_id(id)` — returns User or None
- `get_password_hash(username)` — returns the hash string or None
- `create_user(username, hashed_password)` — inserts user, returns User
- `set_user_online(user_id, status)` — updates is_online
- `save_message(sender_id, message, room_id=None, recipient_id=None)` — inserts message, returns the message text
- `get_unread_dms(user_id)` — returns list of unread DM dicts
- `mark_message_read(user_id, sender_id)` — sets is_read to TRUE

### `server/auth.py`

Functions already built:
- `hash_password(password)` — SHA-256 hash of the password
- `register_user(username, password)` — returns dict with success, message, user
- `login_user(username, password)` — returns dict with success, message, user

### `server/handler.py`

Functions already built:
- `connected_clients` — dict mapping user_id to websocket
- `register_client(user_id, websocket)` — adds to connected_clients
- `unregister_client(user_id)` — removes from connected_clients, sets user offline
- `send_to_client(user_id, message)` — sends JSON to a specific client
- `broadcast_to_room(room_id, message, exclude_user_id=None)` — sends to all room members
- `handle_message(websocket, raw_message)` — parses JSON, routes by type
- `handle_register(websocket, data)` — registers a new user
- `handle_login(websocket, data)` — logs in, registers client, sets online
- `handle_ping(websocket, data)` — responds with pong

### `server/main.py`

Entry point. Reads SERVER_HOST and SERVER_PORT from environment, starts WebSocket server, handles per-client connection loop.

### `client/connection.py`

Functions already built:
- `connect(server_url)` — async, opens WebSocket connection
- `send(websocket, message)` — async, sends dict as JSON
- `receive(websocket)` — async, receives JSON as dict
- `disconnect(websocket)` — async, closes connection

---

## Message Protocol

All communication is JSON over WebSocket. Every message has a `type` field.

### Foundation (already working)

**Client → Server:**
```json
{ "type": "register", "username": "...", "password": "..." }
{ "type": "login", "username": "...", "password": "..." }
{ "type": "ping" }
```

**Server → Client:**
```json
{ "type": "success", "message": "logged in", "username": "..." }
{ "type": "error", "message": "username already taken" }
{ "type": "pong" }
```

### New types to add (per your assignment)

**Rooms:**
```json
{ "type": "create_room", "name": "dev", "is_private": false }
{ "type": "join_room", "name": "dev" }
{ "type": "room_message", "room_id": 1, "content": "hello" }
{ "type": "list_rooms" }
```

**DMs:**
```json
{ "type": "direct_message", "to": "username", "content": "hey" }
{ "type": "inbox" }
{ "type": "mark_read", "from": "username" }
```

**Friends:**
```json
{ "type": "add_friend", "username": "username" }
{ "type": "accept_friend", "username": "username" }
{ "type": "online_friends" }
```

**Block:**
```json
{ "type": "block", "username": "username" }
```

**Invites:**
```json
{ "type": "invite", "room_id": 1, "username": "username" }
```

**Server responses for new types:**
```json
{ "type": "room_message", "from": "nirwan", "room": "dev", "content": "hello", "timestamp": "..." }
{ "type": "direct_message", "from": "nirwan", "content": "hey", "timestamp": "..." }
{ "type": "room_list", "rooms": [...] }
{ "type": "inbox_result", "messages": [...] }
{ "type": "online_friends_result", "users": [...] }
{ "type": "invite_received", "room": "secret", "from": "nirwan" }
{ "type": "error", "message": "user not found" }
{ "type": "success", "message": "joined room" }
```

---

## Work Assignment

Each person works on a `feature/<your-branch>` branch. **Pull from `dev` every morning** before starting work.

When you finish, open a PR into `dev` and message the group.

---

### Paru Maharjan — Server: Rooms

**Your files:** `server/db.py` and `server/handler.py`

You are adding new functions to existing files. Do not change any code that already exists. Only add new functions at the bottom of each file.

#### Week 1

**`server/db.py` — add these functions:**

`create_room(name, is_private, owner_id) → Room`
- INSERT a new row into the `rooms` table with the given name, privacy setting, and owner
- Use RETURNING to get the inserted row back
- Return a Room dataclass with the result

`get_room_by_name(name) → Room | None`
- SELECT from `rooms` WHERE room_name matches the input
- Return a Room dataclass if found, None if not

`get_public_rooms() → list[Room]`
- SELECT all rows from `rooms` WHERE is_private is FALSE
- Return a list of Room dataclasses

`add_room_member(room_id, user_id)`
- INSERT into `room_members` with the given room_id and user_id
- This adds a user to a room
- Use ON CONFLICT DO NOTHING so it doesn't error if the user is already a member

`get_room_members(room_id) → list[User]`
- SELECT all users who are members of the given room
- JOIN `room_members` with `users` on user_id
- Return a list of User dataclasses

`is_room_member(room_id, user_id) → bool`
- SELECT COUNT(*) from `room_members` WHERE room_id and user_id match
- Return True if count > 0, False otherwise

**`server/handler.py` — add these handlers:**

`handle_create_room(websocket, data, user_id)`
- Read name and is_private from data
- Call db.create_room(name, is_private, user_id)
- Call db.add_room_member(room_id, user_id) to auto-add the creator
- Send back success with room info

`handle_join_room(websocket, data, user_id)`
- Read room name from data
- Look up the room with db.get_room_by_name(name)
- If room not found, send error
- If room is private, send error (can't join private rooms without invite)
- Call db.add_room_member(room_id, user_id)
- Send back success

`handle_list_rooms(websocket, user_id)`
- Call db.get_public_rooms()
- Send back a message with type "room_list" containing the list of rooms

**Also:** Add routing in `handle_message`. Add elif blocks for "create_room", "join_room", "list_rooms" that call your handlers. You need to track which user is sending the message — you can get the user_id from connected_clients by matching the websocket object.

#### Week 2

**`server/handler.py` — add this handler:**

`handle_room_message(websocket, data, user_id)`
- Read room_id and content from data
- Check if user is a member of the room with db.is_room_member
- If not a member, send error
- Call db.save_message(sender_id=user_id, content=content, room_id=room_id)
- Get room members with db.get_room_members(room_id)
- Send the message to all connected members of the room using send_to_client
- Do not send back to the sender (they already see their own message)

**Also:** Add routing for "room_message" in handle_message.

**Testing:** After week 2, you should be able to create a room, join it, list rooms, and send messages to the room. Test by running the server with `docker compose up` and using the test client or your own script.

---

### Bipana Khadka — Server: DMs + Invites

**Your files:** `server/db.py` and `server/handler.py`

DM functions (`save_message`, `get_unread_dms`, `mark_messages_read`) already exist in db.py. You are adding invite functions and DM handlers.

#### Week 1

**`server/db.py` — add these functions:**

`is_room_owner(room_id, user_id) → bool`
- SELECT from `rooms` WHERE id matches room_id AND owner_id matches user_id
- Return True if found, False otherwise

`invite_to_room(room_id, inviter_id, invitee_id)`
- Check that the inviter is the room owner with is_room_owner
- If not the owner, return False
- Check that the invitee is not already a member with is_room_member (you'll need to call the function Person 1 writes — if it doesn't exist yet, write a temporary version or wait for their merge)
- Add the invitee as a room member with add_room_member
- Return True on success

**`server/handler.py` — add these handlers:**

`handle_direct_message(websocket, data, user_id)`
- Read "to" (username) and "content" from data
- Look up the recipient with db.get_user_by_username(to)
- If not found, send error "user not found"
- Check if blocked with db.is_blocked(user_id, recipient_id) — if Person 3 hasn't written this yet, skip the check for now and add it after their merge
- If blocked, send error "cannot send message to this user"
- Call db.save_message(sender_id=user_id, content=content, recipient_id=recipient_id)
- Send success to sender
- If recipient is in connected_clients, send them a direct_message notification

`handle_inbox(websocket, user_id)`
- Call db.get_unread_dms(user_id)
- Send back a message with type "inbox_result" containing the list of unread messages

`handle_mark_read(websocket, data, user_id)`
- Read "from" (username) from data
- Look up the sender with db.get_user_by_username(from)
- Call db.mark_message_read(user_id, sender_id)
- Send back success

**Also:** Add routing in handle_message for "direct_message", "inbox", "mark_read".

#### Week 2

**`server/handler.py` — add this handler:**

`handle_invite(websocket, data, user_id)`
- Read room_id and username from data
- Look up the invitee with db.get_user_by_username(username)
- If not found, send error
- Call db.invite_to_room(room_id, user_id, invitee_id)
- If failed (not owner, etc.), send error
- If invitee is online (in connected_clients), send them an invite_received notification
- Send success to inviter

**Also:** Add routing for "invite" in handle_message.

**Testing:** After week 2, you should be able to send DMs, check inbox, mark messages as read, and invite users to private rooms. Test with two terminal windows running the test client.

---

### Suryansh Bikram Shah — Server: Friends + Block

**Your files:** `server/db.py` and `server/handler.py`

#### Week 1

**`server/db.py` — add these functions:**

`send_friend_request(user_id, friend_id)`
- INSERT into `friendships` with user_id, friend_id, and status 'pending'
- If the pair already exists (UNIQUE constraint), do nothing (ON CONFLICT DO NOTHING)
- This is one-directional: user_id sends to friend_id

`accept_friend_request(user_id, friend_id)`
- UPDATE `friendships` SET status = 'accepted' WHERE user_id and friend_id match AND status is 'pending'
- This accepts a request that the other user sent

`decline_friend_request(user_id, friend_id)`
- DELETE from `friendships` WHERE user_id and friend_id match AND status is 'pending'
- This removes the pending request

`get_friends(user_id) → list[User]`
- SELECT all users where a friendship exists between user_id and friend_id with status 'accepted'
- UNION with all users where a friendship exists between friend_id and user_id with status 'accepted'
- This gets friends regardless of who sent the request
- Return a list of User dataclasses

`get_online_friends(user_id) → list[User]`
- Same as get_friends but also filter WHERE is_online is TRUE
- Return a list of User dataclasses

**`server/handler.py` — add these handlers:**

`handle_add_friend(websocket, data, user_id)`
- Read username from data
- Look up the target user with db.get_user_by_username(username)
- If not found, send error
- If trying to add yourself, send error
- Call db.send_friend_request(user_id, friend_id)
- Send success
- If target user is online, send them a notification that they have a friend request

`handle_accept_friend(websocket, data, user_id)`
- Read username from data
- Look up the other user with db.get_user_by_username(username)
- If not found, send error
- Call db.accept_friend_request(user_id, friend_id)
- Send success to both users if the other is online

`handle_online_friends(websocket, user_id)`
- Call db.get_online_friends(user_id)
- Send back a message with type "online_friends_result" containing the list of online friends

**Also:** Add routing in handle_message for "add_friend", "accept_friend", "online_friends".

#### Week 2

**`server/db.py` — add these functions:**

`block_user(user_id, target_id)`
- UPDATE `friendships` SET status = 'blocked' WHERE user_id and friend_id match
- If no row exists, INSERT a new row with status 'blocked'
- This blocks the target from contacting you

`is_blocked(sender_id, recipient_id) → bool`
- SELECT from `friendships` WHERE user_id = recipient_id AND friend_id = sender_id AND status = 'blocked'
- Return True if found (the recipient has blocked the sender)
- Also check the reverse direction

**`server/handler.py` — add this handler:**

`handle_block(websocket, data, user_id)`
- Read username from data
- Look up the target with db.get_user_by_username(username)
- If not found, send error
- Call db.block_user(user_id, target_id)
- Send success

**Also:** Add routing for "block" in handle_message.

**Testing:** After week 2, you should be able to send friend requests, accept them, see online friends, and block users. Test with multiple client connections.

---

### Subista Kunwar — Client: Commands + UI + Main

**Your files:** `client/commands.py`, `client/ui.py`, `client/main.py`

You are building the entire client side. The server team is building in parallel — you can work against the existing protocol (register, login, ping) in week 1 and add the rest in week 2.

#### Week 1

**`client/commands.py` — build from scratch:**

`parse_input(raw: str) → dict`
- Takes a raw string the user typed
- If it starts with `/`, it is a command — parse the command word and arguments
- If it does not start with `/`, it is a chat message for the current room
- Return a dict with a "type" field and relevant data
- Examples:
  - `"/dm nirwan hello"` → `{"type": "direct_message", "to": "nirwan", "content": "hello"}`
  - `"/rooms"` → `{"type": "list_rooms"}`
  - `"/join dev"` → `{"type": "join_room", "name": "dev"}`
  - `"/create dev"` → `{"type": "create_room", "name": "dev"}`
  - `"/help"` → `{"type": "help"}`
  - `"/quit"` → `{"type": "quit"}`
  - `"hello everyone"` → `{"type": "room_message", "content": "hello everyone"}`
- For commands that need arguments (like /dm), validate that the argument exists. If not, return an error dict.

`get_command_list() → list[str]`
- Return a list of strings, each being a command and its description
- Example: `["/dm username message    Send a direct message", "/rooms                  List all public rooms", ...]`
- This is used by the /help command

**`client/ui.py` — build from scratch:**

All rendering uses the `rich` library. Import `from rich.console import Console` and create a console instance. No print() calls anywhere else.

`print_welcome()`
- Print a welcome banner using rich
- Show the app name and basic instructions
- Example: a rich Panel with "Welcome to UamiChat" and "Type /help for commands"

`print_message(username, content, timestamp)`
- Print a single chat message formatted with username, content, and timestamp
- Use rich formatting to make the username stand out (bold or colored)

`print_system(message)`
- Print a system notification in a distinct color (yellow or cyan)
- Used for join/leave events, server notifications

`print_error(message)`
- Print an error message in red
- Used for validation errors, server errors

`print_help(commands)`
- Print the full command list in a rich Panel or Table
- Takes the output of get_command_list() as input

`print_room_list(rooms)`
- Print a table of public rooms with columns: Name, Members, Created
- Takes a list of room dicts as input

`clear_screen()`
- Clear the terminal for a clean state on login
- Use `os.system("clear")` or rich's console.clear()

#### Week 2

**`client/commands.py` — add remaining commands to parse_input:**

- `"/invite username"` → `{"type": "invite", "username": "username"}`
- `"/inbox"` → `{"type": "inbox"}`
- `"/online"` → `{"type": "online_friends"}`
- `"/addfriend username"` → `{"type": "add_friend", "username": "username"}`
- `"/block username"` → `{"type": "block", "username": "username"}`

**`client/ui.py` — add remaining functions:**

`print_inbox(messages)`
- Print unread DMs in a table with columns: From, Message, Time
- Takes a list of message dicts as input

`print_online_friends(users)`
- Print a list of online friends
- Takes a list of user dicts as input

**`client/main.py` — build from scratch:**

This is the entry point that ties everything together.

`prompt_login() → dict`
- Prompt the user for username and password using rich prompts
- Return `{"username": "...", "password": "..."}`

`prompt_register() → dict`
- Prompt for username, password, and password confirmation
- If passwords don't match, show error and re-prompt
- Return `{"username": "...", "password": "..."}`

`listen(websocket)`
- An async function that runs in a background task
- Continuously calls connection.receive(websocket)
- For each message received, check the type and call the appropriate ui function:
  - "room_message" → print_message
  - "direct_message" → print_message
  - "inbox_result" → print_inbox
  - "online_friends_result" → print_online_friends
  - "invite_received" → print_system
  - "error" → print_error
  - "success" → print_system
- On ConnectionClosed, print "Disconnected from server"

`input_loop(websocket)`
- An async function that runs in a background task
- Continuously reads user input with `await asyncio.get_event_loop().run_in_executor(None, input, "> ")`
- Passes input to commands.parse_input
- If the result type is "quit", disconnect and exit
- Otherwise, send the result to the server with connection.send
- Handle any send errors gracefully

`main()`
- Entry point. Show welcome banner with print_welcome()
- Ask user to login or register
- Connect to server with connection.connect
- Send register or login message
- Wait for server response
- On success, clear screen and start listen and input_loop as concurrent asyncio tasks
- On failure, show error and exit

---

## Running Tests

Unit and integration tests live in `tests/` and use `pytest`. One test file per feature.

```bash
# install test dependencies (includes the regular ones)
uv pip install -r requirements-dev.txt

# run everything
pytest

# run a single file
pytest tests/test_client_week1.py
```

Handler tests are unit tests that mock the database layer. Tests that touch the database use a dedicated `uamichat_test` database so development data is never polluted. It is created on the docker Postgres once:

```bash
# create the test database (first time only)
docker compose exec -T db psql -U uami -d uamichat -c "CREATE DATABASE uamichat_test"
docker compose exec -T db psql -U uami -d uamichat_test -f /docker-entrypoint-initdb.d/schema.sql

# override the test DB URL if it is not at the default location
# TEST_DB_URL=postgresql://uami@localhost:5433/uamichat_test pytest
```

---

## Testing Checklist

After all four people have merged their work, verify these flows:

- [x] Register a new user
- [x] Login with existing user
- [x] Create a public room
- [x] Join a public room
- [x] List public rooms
- [x] Send a message in a room
- [x] Send a DM to another user
- [x] Check inbox for unread DMs
- [x] Mark DMs as read
- [x] Send a friend request
- [x] Accept a friend request
- [x] See online friends
- [x] Block a user
- [x] Invite someone to a private room
- [x] /help shows all commands
- [x] /quit disconnects cleanly

---

## Commands Reference

```
/dm username message       send a direct message
/rooms                     list all public rooms
/join roomname             join a public room
/create roomname           create a new room
/invite username           invite someone to your private room
/inbox                     show unread direct messages
/online                    show online friends
/addfriend username        send a friend request
/block username            block a user
/help                      list all available commands
/quit                      disconnect and exit
```
