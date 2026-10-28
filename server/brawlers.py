"""v29 brawler catalog (characters.csv / cards.csv) and power-level costs."""

# character ID -> (unlock card row in cards.csv, rarity)
BRAWLERS = {
    0: (0, 'common'), 1: (4, 'common'), 2: (8, 'common'), 3: (12, 'common'),
    4: (16, 'super_rare'), 5: (20, 'legendary'), 6: (24, 'rare'), 7: (28, 'common'),
    8: (32, 'common'), 9: (36, 'common'), 10: (40, 'rare'), 11: (44, 'mega_epic'),
    12: (48, 'legendary'), 13: (52, 'rare'), 14: (56, 'common'), 15: (60, 'epic'),
    16: (64, 'epic'), 17: (68, 'mega_epic'), 18: (72, 'super_rare'), 19: (95, 'super_rare'),
    20: (100, 'epic'), 21: (105, 'mega_epic'), 22: (110, 'common'), 23: (115, 'legendary'),
    24: (120, 'rare'), 25: (125, 'super_rare'), 26: (130, 'epic'), 27: (177, 'common'),
    28: (182, 'legendary'), 29: (188, 'epic'), 30: (194, 'common'), 31: (200, 'mega_epic'),
    32: (206, 'mega_epic'), 34: (218, 'super_rare'), 35: (224, 'epic'), 36: (230, 'epic'),
    37: (236, 'mega_epic'), 38: (279, 'epic'),
    39: (296, 'epic'),  # Colette: Brawl Pass season 2 brawler and a free shop offer.
}
UNLOCK_CARDS = {brawler: card for brawler, (card, _) in BRAWLERS.items()}

# Brawlers that can drop from boxes, by rarity weight (common ones come from Trophy Road).
BOX_EXCLUDED = {39}  # Colette comes from the Brawl Pass and her free offer.
BOX_RARITY_WEIGHTS = {'rare': 50, 'super_rare': 25, 'epic': 13, 'mega_epic': 8, 'legendary': 4}

# Upgrading from power level N+1 to N+2 costs UPGRADE_POINTS[N] points and UPGRADE_GOLD[N] coins.
UPGRADE_POINTS = (20, 30, 50, 80, 130, 210, 340, 550)
UPGRADE_GOLD = (20, 35, 75, 140, 290, 480, 800, 1250)
MAX_POWER_POINTS = sum(UPGRADE_POINTS)
MAX_LEVEL = len(UPGRADE_POINTS)  # Native numbering: 8 is power 9.

# Star power and gadget cards (cards.csv rows) a fully kitted brawler owns:
# its released star powers, then its gadget. Cards marked LockedForChronos
# (unreleased in v29, such as Colette's second star power 301) are left out.
EXTRA_CARDS = {
    0: (76, 135, 255), 1: (77, 138, 273), 2: (78, 137, 272), 3: (79, 150, 245),
    4: (80, 156, 246), 5: (81, 151, 247), 6: (82, 158, 250), 7: (83, 149, 251),
    8: (84, 136, 249), 9: (85, 155, 258), 10: (86, 140, 264), 11: (87, 154, 265),
    12: (88, 143, 243), 13: (89, 144, 267), 14: (90, 148, 263), 15: (91, 152, 268),
    16: (92, 139, 257), 17: (93, 160, 266), 18: (94, 157, 260), 19: (99, 142, 248),
    20: (104, 153, 261), 21: (109, 159, 252), 22: (114, 161, 253), 23: (119, 141, 276),
    24: (124, 147, 242), 25: (129, 145, 262), 26: (134, 146, 275), 27: (168, 181, 259),
    28: (186, 187, 270), 29: (192, 193, 271), 30: (198, 199, 274), 31: (204, 205, 269),
    32: (210, 211, 254), 34: (222, 223, 256), 35: (228, 229, 277), 36: (234, 235, 278),
    37: (240, 241, 244), 38: (283, 285), 39: (300, 302),
}

NAMES = {
    0: 'Shelly', 1: 'Colt', 2: 'Bull', 3: 'Brock', 4: 'Rico', 5: 'Spike', 6: 'Barley',
    7: 'Jessie', 8: 'Nita', 9: 'Dynamike', 10: 'El Primo', 11: 'Mortis', 12: 'Crow',
    13: 'Poco', 14: 'Bo', 15: 'Piper', 16: 'Pam', 17: 'Tara', 18: 'Darryl', 19: 'Penny',
    20: 'Frank', 21: 'Gene', 22: 'Tick', 23: 'Leon', 24: 'Rosa', 25: 'Carl', 26: 'Bibi',
    27: '8-Bit', 28: 'Sandy', 29: 'Bea', 30: 'Emz', 31: 'Mr. P', 32: 'Max', 34: 'Jacky',
    35: 'Gale', 36: 'Nani', 37: 'Sprout', 38: 'Surge', 39: 'Colette',
}


def find(name):
    """Brawler ID from a name (case, spaces and punctuation ignored) or a number."""
    key = ''.join(c for c in name.lower() if c.isalnum())
    if key.isdigit() and int(key) in BRAWLERS:
        return int(key)
    for brawler, label in NAMES.items():
        if ''.join(c for c in label.lower() if c.isalnum()) == key:
            return brawler
    return None


def owned(player):
    return player.setdefault('unlocked', [0])


def power_level(player, brawler):
    """Stored as 0 for power 1 (the client's native numbering)."""
    return player.get('power_levels', {}).get(str(brawler), 0)


def points(player, brawler):
    """Lifetime power points, including those already used for upgrades (native numbering)."""
    return player.get('power_points', {}).get(str(brawler), 0)


def spare_points(player, brawler):
    """Points collected towards the next power level."""
    return points(player, brawler) - sum(UPGRADE_POINTS[:power_level(player, brawler)])


def points_needed(player, brawler):
    """Points the brawler can still use before reaching power 9."""
    return max(0, MAX_POWER_POINTS - points(player, brawler))


def add_points(player, brawler, amount):
    stored = player.setdefault('power_points', {})
    stored[str(brawler)] = stored.get(str(brawler), 0) + amount


def cards(player):
    """Owned star power and gadget cards."""
    return player.setdefault('cards', [])


def maxed(player, brawler):
    return (brawler in owned(player) and power_level(player, brawler) >= MAX_LEVEL
            and all(card in cards(player) for card in EXTRA_CARDS.get(brawler, ())))


def max_out(player, brawler):
    """Unlock the brawler at power 9 with all its star powers and gadgets."""
    if brawler not in owned(player):
        owned(player).append(brawler)
    player.setdefault('power_levels', {})[str(brawler)] = MAX_LEVEL
    stored = player.setdefault('power_points', {})
    stored[str(brawler)] = max(stored.get(str(brawler), 0), MAX_POWER_POINTS)
    for card in EXTRA_CARDS.get(brawler, ()):
        if card not in cards(player):
            cards(player).append(card)


def upgrade(player, brawler):
    """Raise one power level, spending points and coins. Returns the new level or None."""
    if brawler not in owned(player):
        return None
    level = power_level(player, brawler)
    if level >= len(UPGRADE_POINTS):
        return None
    need, cost = UPGRADE_POINTS[level], UPGRADE_GOLD[level]
    if spare_points(player, brawler) < need or player.get('gold', 0) < cost:
        return None
    player['gold'] -= cost  # Points stay counted: the client tracks lifetime totals.
    player.setdefault('power_levels', {})[str(brawler)] = level + 1
    return level + 1
