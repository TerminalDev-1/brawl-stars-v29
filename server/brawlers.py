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
}
UNLOCK_CARDS = {brawler: card for brawler, (card, _) in BRAWLERS.items()}

# Brawlers that can drop from boxes, by rarity weight (common ones come from Trophy Road).
BOX_RARITY_WEIGHTS = {'rare': 50, 'super_rare': 25, 'epic': 13, 'mega_epic': 8, 'legendary': 4}

# Upgrading from power level N+1 to N+2 costs UPGRADE_POINTS[N] points and UPGRADE_GOLD[N] coins.
UPGRADE_POINTS = (20, 30, 50, 80, 130, 210, 340, 550)
UPGRADE_GOLD = (20, 35, 75, 140, 290, 480, 800, 1250)
MAX_POWER_POINTS = sum(UPGRADE_POINTS)


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
