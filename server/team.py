"""Single-player team rooms with team chat, used for /dev commands.

Message IDs (v29): the client sends TeamCreate 14350, TeamLeave 14353 and
TeamChat 14359; the server answers with TeamMessage 24124, TeamStream 24131
(chat entries) and TeamLeaveOk 24125.
"""
import itertools
import time

from protocol import Reader, Writer

TEAM_CREATE, TEAM_LEAVE, TEAM_CHAT = 14350, 14353, 14359
TEAM_MESSAGE, TEAM_LEAVE_OK, TEAM_STREAM = 24124, 24125, 24131
CHAT_ENTRY = 2
SERVER_NAME = 'Server'

_room_ids = itertools.count(1)


class Room:
    def __init__(self, room_type, map_id):
        self.id = next(_room_ids)
        self.room_type = room_type
        self.map_id = map_id
        self.tick = 0


def read_create(payload):
    """(room type, map) from TeamCreate. Unknown layouts fall back to defaults."""
    r = Reader(payload)
    try:
        r.vint()  # Event slot.
        table = r.vint()
        map_id = r.vint() if table else 0
        room_type = r.vint()
    except ValueError:
        return 0, 0
    return room_type, map_id


def read_chat(payload):
    return (Reader(payload).string() or '').strip()


def team_message(player, room):
    """TeamMessage, following the reference v29 server's field order."""
    w = Writer()
    w.values(room.room_type, 0, 3, 0, 0, 0, 0)  # Type, state, max players, ...
    w.integer(room.id)
    w.values(int(time.time()), 0, 0, 0)
    w.reference(15, room.map_id)
    w.values(1, 1)  # One member, who owns the room.
    w.integer(0)
    w.integer(player['id'])
    brawler = player.get('brawler', 0)
    trophies = (player.get('brawler_trophies') or {}).get(str(brawler), 0)
    w.reference(16, brawler)
    w.reference(29, (player.get('skins') or {}).get(str(brawler), 0))
    w.values(trophies, trophies, player.get('power_levels', {}).get(str(brawler), 0) + 1)  # Power
    w.values(0, 0, 0, 0, 0)  # Status, ready, unknown.
    w.string(player['name'])
    w.values(100, 28000000 + player['icon'], 43000000 + player['name_color'], 0, 0, 0)
    w.values(0, 0, 0, 0, 6)  # No invites, then trailing fields.
    return w.bytes()


def chat_entry(room, sender_id, name, text):
    """TeamStream with one chat entry, following the reference v29 server."""
    room.tick += 1
    w = Writer()
    w.values(0, room.id, 1)
    w.values(CHAT_ENTRY, 0, room.tick, 0, sender_id)
    w.string(name)
    w.values(0, 0, 0)  # Unknown, age in seconds, flag.
    w.string(text)
    return w.bytes()


def leave_ok():
    w = Writer()
    w.integer(0)
    return w.bytes()
