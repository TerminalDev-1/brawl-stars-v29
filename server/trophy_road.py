"""v29 Trophy Road table (milestones.csv track 6) and reward delivery."""
import secrets

from protocol import Writer

# Reward types used by milestones.csv.
GOLD, BRAWLER, BRAWL_BOX, TOKEN_DOUBLER, MEGA_BOX = 1, 3, 6, 9, 10
POWER_POINTS, MODE_UNLOCK, BIG_BOX, FEATURE_UNLOCK = 12, 13, 14, 18

# Delivery box IDs understood by the client's reward screen.
DELIVERY_BOX = {BRAWL_BOX: 10, BIG_BOX: 12, MEGA_BOX: 11}
SINGLE_REWARD = 100

# Item types inside a delivery.
ITEM_BRAWLER, ITEM_TOKEN_DOUBLER, ITEM_POWER_POINTS, ITEM_GOLD, ITEM_GEMS = 1, 2, 6, 7, 8

# character ID -> unlock card row (cards.csv) for Shelly and Trophy Road brawlers.
UNLOCK_CARDS = {0: 0, 1: 4, 2: 8, 3: 12, 7: 28, 8: 32, 9: 36, 14: 56, 22: 110, 27: 177, 30: 194}

# (trophies required, reward type, amount, character ID) for milestone indices 0-93.
_EARLY = [
    (5, 6, 1, None), (10, 3, 1, 8), (20, 6, 1, None), (30, 13, 0, None), (40, 6, 1, None),
    (60, 3, 1, 1), (100, 9, 200, None), (150, 13, 0, None), (200, 12, 25, None),
    (250, 3, 1, 2), (300, 18, 0, None), (350, 13, 0, None), (400, 12, 25, None),
    (450, 6, 1, None), (500, 3, 1, 7), (550, 1, 50, None), (600, 12, 25, None),
    (650, 14, 1, None), (700, 1, 50, None), (750, 6, 1, None), (800, 13, 0, None),
    (850, 12, 25, None), (900, 1, 50, None), (950, 14, 1, None), (1000, 3, 1, 3),
    (1100, 1, 50, None), (1200, 6, 1, None), (1300, 12, 75, None), (1400, 1, 100, None),
    (1500, 12, 50, None), (1600, 14, 1, None), (1700, 1, 50, None), (1800, 14, 1, None),
    (1900, 12, 50, None), (2000, 3, 1, 9), (2100, 1, 50, None), (2200, 6, 1, None),
    (2300, 12, 150, None), (2400, 1, 50, None), (2500, 6, 1, None), (2600, 1, 150, None),
    (2700, 6, 1, None), (2800, 12, 25, None), (2900, 1, 50, None), (3000, 3, 1, 14),
    (3100, 1, 50, None), (3200, 12, 25, None), (3300, 1, 300, None), (3400, 6, 1, None),
    (3500, 1, 50, None), (3600, 9, 600, None), (3700, 6, 1, None), (3800, 12, 25, None),
    (3900, 1, 50, None), (4000, 3, 1, 22), (4150, 12, 150, None), (4300, 1, 200, None),
    (4500, 14, 1, None), (4750, 12, 25, None), (5000, 10, 1, None), (5150, 12, 25, None),
    (5300, 6, 1, None), (5500, 1, 150, None), (5750, 12, 25, None), (6000, 3, 1, 27),
    (6150, 1, 200, None), (6300, 14, 1, None), (6500, 12, 150, None), (6750, 1, 200, None),
    (7000, 10, 1, None), (7150, 1, 50, None), (7300, 12, 25, None), (7500, 14, 1, None),
    (7750, 1, 50, None), (8000, 3, 1, 30), (8150, 14, 1, None), (8300, 12, 150, None),
    (8500, 14, 1, None), (8750, 1, 200, None), (9000, 10, 1, None), (9150, 1, 150, None),
    (9300, 12, 50, None), (9500, 1, 150, None), (9750, 14, 1, None), (10000, 10, 1, None),
    (10500, 1, 500, None), (11000, 10, 1, None), (11500, 12, 200, None), (12000, 10, 1, None),
    (12500, 1, 500, None), (13000, 10, 1, None), (13500, 12, 100, None), (14000, 10, 1, None),
    (14500, 1, 1000, None),
]
# From 15,000 to 50,000 trophies the road alternates Mega Box / Big Box every 500.
TROPHY_ROAD = _EARLY + [(t, MEGA_BOX if t % 1000 == 0 else BIG_BOX, 1, None)
                        for t in range(15000, 50001, 500)]

POWER_POINT_CAP = 1410  # Points needed to take a brawler from power 1 to 9.


def unlocked(player):
    return player.setdefault('unlocked', [0])


def add_points(player, brawler, amount):
    points = player.setdefault('power_points', {})
    points[str(brawler)] = points.get(str(brawler), 0) + amount


def _box_items(player, box):
    """Random box contents: coins, power points, sometimes gems."""
    scale = {BRAWL_BOX: 1, BIG_BOX: 3, MEGA_BOX: 10}[box]
    owned = unlocked(player)
    items = [(ITEM_GOLD, None, scale * (15 + secrets.randbelow(26)))]
    picks = owned if len(owned) <= scale else [owned[secrets.randbelow(len(owned))] for _ in range(scale)]
    for brawler in dict.fromkeys(picks):
        items.append((ITEM_POWER_POINTS, brawler, scale * (7 + secrets.randbelow(14))))
    if secrets.randbelow(4) == 0:
        items.append((ITEM_GEMS, None, scale * (1 + secrets.randbelow(3))))
    return items


def claim(player):
    """Apply the next Trophy Road reward to player state.

    Returns (milestone index, delivery box ID, items) or None if nothing is claimable.
    """
    index = player.get('trophy_road', 1) - 1
    if index >= len(TROPHY_ROAD):
        return None
    required, kind, amount, character = TROPHY_ROAD[index]
    if player.get('highest_trophies', player['trophies']) < required:
        return None
    if kind in DELIVERY_BOX:
        box, items = DELIVERY_BOX[kind], _box_items(player, kind)
    elif kind == BRAWLER:
        if character in unlocked(player):  # Already owned: give the matching points instead.
            box, items = SINGLE_REWARD, [(ITEM_POWER_POINTS, character, 100)]
        else:
            box, items = SINGLE_REWARD, [(ITEM_BRAWLER, character, 1)]
    elif kind == GOLD:
        box, items = SINGLE_REWARD, [(ITEM_GOLD, None, amount)]
    elif kind == POWER_POINTS:
        box, items = SINGLE_REWARD, [(ITEM_POWER_POINTS, player.get('brawler', 0), amount)]
    elif kind == TOKEN_DOUBLER:
        box, items = SINGLE_REWARD, [(ITEM_TOKEN_DOUBLER, None, amount)]
    else:  # Game-mode and feature unlocks have nothing to hand out.
        box, items = SINGLE_REWARD, []
    for item, brawler, count in items:
        if item == ITEM_GOLD:
            player['gold'] = player.get('gold', 0) + count
        elif item == ITEM_GEMS:
            player['gems'] = player.get('gems', 0) + count
        elif item == ITEM_POWER_POINTS:
            add_points(player, brawler, count)
        elif item == ITEM_BRAWLER:
            unlocked(player).append(brawler)
        elif item == ITEM_TOKEN_DOUBLER:
            player['token_doubler'] = player.get('token_doubler', 0) + count
    player['trophy_road'] = index + 2
    return index, box, items


def delivery_command(box, items, track, new_counter):
    """AvailableServerCommand (24111) carrying LogicGiveDeliveryItemsCommand (203)."""
    w = Writer()
    w.values(203, 0, 1, box, len(items))
    for item, brawler, count in items:
        w.vint(count)
        if brawler is None:
            w.vint(0)
        else:
            w.reference(16, brawler)
        w.values(item, 0, 0, 0, 0)
    w.boolean(False)
    w.values(track, new_counter, 0, 1)
    return w.bytes()
