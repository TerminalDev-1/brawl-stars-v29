"""Minimal v29 login and home-state serialization, without battle simulation."""
import time
from protocol import Writer


def login_ok(player, token):
    w = Writer()
    w.long(player['id'])
    w.long(player['id'])
    for value in [token, None, None]:
        w.string(value)
    for value in [29, 270, 1]:
        w.integer(value)
    w.string('dev')
    for value in [1, 0, 0]:
        w.integer(value)
    for _ in range(3):
        w.string()
    w.integer(0)
    w.string()
    w.string('GB')
    w.string()
    w.integer(1)
    for _ in range(3):
        w.string()
    w.vint(0)
    w.string()
    w.vint(1)
    return w.bytes()


def event(w, slot, map_id):
    w.values(slot, slot, 0, 3600, 10)
    w.reference(15, map_id)
    w.vint(2)
    w.string('')
    w.values(2, 0, 3, 0, 0, 0)


def home_data(p):
    w = Writer()
    # Daily data: progression, cosmetics, timers, shop, selected character.
    w.values(int(time.time()), 0, p['trophies'], p['trophies'], p['trophies'], 1, 220)
    w.reference(28, p['icon'])
    w.reference(43, p['name_color'])
    w.values(0, 1)
    w.reference(29, 0)
    w.values(0, 0, 0, p['trophies'], 0, 0)
    w.boolean(False)
    w.values(0, 3600000, 0, 3600000, 0)
    w.boolean(True)
    w.boolean(True)
    w.values(0, 4, 2, 2, 2, 0, 0)
    w.vint(0)  # no shop offers
    w.values(0, 200, 0, 0, 0, 0)  # ads, tokens, timers, tickets
    w.reference(16, p['brawler'])
    w.string('GB')
    w.string('')
    w.values(0, 0)  # settings and countdown arrays
    w.boolean(True)
    w.values(0, 0, 0, 0)
    for _ in range(2):
        w.boolean(True)
        for _ in range(4):
            w.integer(0)
    w.values(1, 0, 0)
    w.boolean(True)
    w.vint(0)  # quests
    w.boolean(True)
    w.vint(0)  # emotes
    # Regional configuration and event slots.
    w.values(int(time.time()), 100, 10, 30, 3, 80, 10, 40, 1500, 500, 50, 999900, 0)
    w.values(2, 0, 1, 1)
    event(w, 1, 7)
    w.vint(0)  # upcoming events
    for values in [(20, 35, 75, 140, 290, 480, 800, 1250), (1, 2, 3, 4, 5, 10, 15, 20),
                   (10, 30, 80), (6, 20, 60), (10,), (1000,)]:
        w.vint(len(values))
        w.values(*values)
    w.values(0, 200, 20, 8640, 10, 5, 6, 50, 604800)
    w.boolean(True)
    w.values(0, 1)
    w.integer(1)
    w.integer(41000000 + p['theme'])
    w.values(0, 0)
    w.long(p['id'])
    w.values(0, 0)  # notification count and initial notification type
    w.boolean(True)
    w.values(0, 0)  # home-state records and string-reference list
    # Avatar: IDs, name, and eight commodity dictionaries.
    for _ in range(3):
        w.values(0, p['id'])
    w.string(p['name'])
    w.vint(1)
    w.integer(0)
    w.values(8, 5)
    for table, row, amount in [(23, 0, 1), (5, 1, 0), (5, 8, p['gold']), (5, 9, 0), (5, 10, 0)]:
        w.reference(table, row)
        w.vint(amount)
    for amount in [p['trophies'], p['trophies'], None, 0, 0, None, None]:
        w.vint(0 if amount is None else 1)
        if amount is not None:
            w.reference(16, p['brawler'])
            w.vint(amount)
    w.values(p['gems'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, int(time.time()))
    return w.bytes()
