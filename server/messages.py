"""Minimal v29 login and home-state serialization, without battle simulation."""
import time
from protocol import Writer
from brawlers import UNLOCK_CARDS
import brawl_pass
import shop

GEM_GRAB_MAP, SHOWDOWN_MAP = 7, 13  # locations.csv: Hard Rock Mine, Skull Creek


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
    best = p.get('highest_trophies', p['trophies'])
    w.values(int(time.time()), 0, p['trophies'], best, best, p.get('trophy_road', 1),
             220 + p.get('experience', 0))
    w.reference(28, p['icon'])
    w.reference(43, p['name_color'])
    w.values(0, 1)  # selected skin of the selected brawler
    w.reference(29, p.get('skins', {}).get(str(p['brawler']), 0))
    w.values(0, 0, 0, best, 0, 0)
    w.boolean(False)
    w.values(p.get('token_doubler', 0), 3600000, 0, 3600000, 0)  # token doubler, season timers
    w.boolean(True)
    w.boolean(True)
    w.values(0, 4, 2, 2, 2, 0, 0)
    shop.encode_offers(w, p)
    w.values(0, 200, 0, 0, 0, 0)  # ads, tokens, timers, tickets
    w.reference(16, p['brawler'])
    w.string('GB')
    w.string('')
    w.values(0, 0)  # settings and countdown arrays
    brawl_pass.encode(w, p)
    w.values(1, 0, 0)
    w.boolean(True)
    w.vint(0)  # quests
    w.boolean(True)
    w.vint(0)  # emotes
    # Regional configuration and event slots.
    w.values(int(time.time()), 100, 10, 30, 3, 80, 10, 40, 1500, 500, 50, 999900, 0)
    w.values(3, 0, 1, 2)  # event slot IDs
    w.vint(2)
    event(w, 1, GEM_GRAB_MAP)
    event(w, 2, SHOWDOWN_MAP)
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
    owned = p.get('unlocked', [0])
    trophies = brawler_trophies(p)
    points = p.get('power_points', {})
    w.values(8, len(owned) + 4)
    for brawler in owned:
        w.reference(23, UNLOCK_CARDS[brawler])
        w.vint(1)
    for table, row, amount in [(5, 1, 0), (5, 8, p['gold']), (5, 9, 0), (5, 10, 0)]:
        w.reference(table, row)
        w.vint(amount)
    for values in [trophies, trophies, None, {b: points.get(str(b), 0) for b in owned},
                   {b: p.get('power_levels', {}).get(str(b), 0) for b in owned}, None, None]:
        values = values or {}
        w.vint(len(values))
        for brawler, amount in values.items():
            w.reference(16, brawler)
            w.vint(amount)
    w.values(p['gems'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, int(time.time()))
    return w.bytes()


def brawler_trophies(p):
    """Per-brawler trophies; accounts from before this existed keep all on Shelly."""
    stored = p.get('brawler_trophies') or {'0': p['trophies']}
    return {b: stored.get(str(b), 0) for b in p.get('unlocked', [0])}
