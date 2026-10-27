"""Brawl Pass season 2 (Starr Park, Colette) from milestones.csv tracks 9 and 10.

Each entry is (tokens needed, reward type, amount, extra). Extra names the
brawler, skin or pin the reward unlocks.
"""
import brawlers
import trophy_road

SEASON = 2
FREE, PREMIUM = 10, 9          # Reward track IDs used in claims and deliveries.
PASS_PRICE = 169               # Gems.
TIER_PRICE = 30                # Gems for the next tier.

FREE_TRACK = [
    (0, 14, 1, None), (75, 6, 1, None), (150, 16, 10, None), (250, 14, 1, None),
    (400, 6, 1, None), (600, 14, 1, None), (900, 1, 50, None), (1300, 14, 1, None),
    (1700, 6, 1, None), (2100, 14, 1, None), (2500, 10, 1, None), (2900, 14, 1, None),
    (3300, 6, 1, None), (3700, 14, 1, None), (4100, 16, 10, None), (4500, 14, 1, None),
    (4900, 6, 1, None), (5300, 14, 1, None), (5700, 1, 50, None), (6100, 14, 1, None),
    (6500, 10, 1, None), (7000, 6, 1, None), (7500, 16, 20, None), (8000, 14, 1, None),
    (8500, 6, 1, None), (9000, 14, 1, None), (9500, 12, 50, None), (10000, 14, 1, None),
    (10500, 6, 1, None), (11000, 14, 1, None), (11500, 10, 1, None), (12000, 14, 1, None),
    (12500, 1, 100, None), (13000, 6, 1, None), (13500, 12, 50, None), (14000, 14, 1, None),
    (14500, 16, 10, None), (15000, 14, 1, None), (15500, 6, 1, None), (16000, 14, 1, None),
    (16500, 10, 1, None), (17100, 6, 1, None), (17700, 12, 75, None), (18300, 6, 1, None),
    (18900, 16, 10, None), (19500, 10, 1, None), (20100, 6, 1, None), (20700, 14, 1, None),
    (21300, 1, 200, None), (21900, 14, 1, None), (22500, 12, 100, None), (23100, 10, 1, None),
    (23700, 16, 10, None), (24300, 14, 1, None), (24900, 6, 1, None), (25500, 10, 1, None),
    (26100, 1, 200, None), (26700, 14, 1, None), (27300, 6, 1, None), (27900, 14, 1, None),
    (28500, 10, 1, None), (29100, 14, 1, None), (29700, 16, 20, None), (30300, 6, 1, None),
    (30900, 12, 100, None), (31500, 10, 1, None), (32100, 14, 1, None), (32700, 1, 500, None),
    (33300, 10, 1, None), (33900, 12, 500, None), (34500, 21, 1, None),
]
PREMIUM_TRACK = [
    (0, 24, 1, 'PocoStarr'), (150, 10, 1, None), (400, 1, 100, None), (900, 14, 1, None),
    (1700, 1, 100, None), (2500, 21, 1, None), (3300, 12, 50, None), (4100, 14, 1, None),
    (4900, 1, 100, None), (5700, 10, 1, None), (6500, 1, 100, None), (7500, 14, 1, None),
    (8500, 12, 100, None), (9500, 14, 1, None), (10500, 1, 200, None),
    (11500, 3, 1, 'Percenter'), (12000, 19, 1, 'emoji_colette_angry'), (12500, 14, 1, None),
    (13000, 19, 1, 'emoji_colette_sad'), (13500, 10, 1, None), (14500, 14, 1, None),
    (15000, 19, 1, 'emoji_colette_happy'), (15500, 12, 100, None), (16500, 1, 200, None),
    (17100, 19, 1, 'emoji_colette_thanks'), (17700, 14, 1, None), (18900, 14, 1, None),
    (19500, 19, 1, 'emoji_colette_gg'), (20100, 12, 200, None), (21300, 10, 1, None),
    (21900, 19, 1, 'emoji_colette_phew'), (22500, 14, 1, None), (23700, 14, 1, None),
    (24300, 19, 1, 'emoji_colette_trixie'), (24900, 1, 200, None), (26100, 14, 1, None),
    (26700, 19, 1, 'emoji_colette_trixie_angry'), (27300, 12, 200, None),
    (27900, 19, 1, 'emoji_colette_trixie_sad'), (28500, 14, 1, None),
    (29100, 19, 1, 'emoji_colette_trixie_happy'), (29700, 10, 1, None),
    (30300, 19, 1, 'emoji_colette_trixie_thanks'), (30900, 14, 1, None),
    (31500, 19, 1, 'emoji_colette_trixie_gg'), (32100, 1, 300, None),
    (32700, 19, 1, 'emoji_colette_trixie_phew'), (33300, 12, 500, None),
    (33900, 19, 1, 'emoji_colette_trixie_special'), (34500, 4, 1, 'PercenterTrixie'),
]

# Reward types in milestones.csv.
R_GOLD, R_BRAWLER, R_SKIN_ALT, R_BRAWL_BOX, R_MEGA_BOX, R_POWER_POINTS = 1, 3, 4, 6, 10, 12
R_BIG_BOX, R_GEMS, R_PIN, R_PIN_PACK, R_SKIN = 14, 16, 19, 21, 24
BOXES = {R_BRAWL_BOX: trophy_road.BRAWL_BOX, R_BIG_BOX: trophy_road.BIG_BOX,
         R_MEGA_BOX: trophy_road.MEGA_BOX}
CHARACTERS = {'Percenter': 39}
SKINS = {'PocoStarr': 214, 'PercenterTrixie': 212}
ITEM_SKIN = 9


def state(player):
    return player.setdefault('brawl_pass', {'tokens': 0, 'premium': False, 'free': 0, 'paid': 0})


def tier(tokens):
    """Tier reached; the free track holds every tier threshold (the client counts the same way)."""
    return sum(1 for needed, *_ in FREE_TRACK if tokens >= needed)


def mask_bit(index):
    return 1 << (index + 2)


def add_tokens(player, amount):
    """Battle tokens, doubled while the Token Doubler lasts. Returns (earned, doubled)."""
    doubled = min(amount, player.get('token_doubler', 0))
    player['token_doubler'] = player.get('token_doubler', 0) - doubled
    state(player)['tokens'] += amount + doubled
    return amount, doubled


def reward_items(player, kind, amount, extra):
    """Delivery (box, items) for one reward, applied to the player."""
    if kind in BOXES:
        items = trophy_road.box_items(player, BOXES[kind])
        trophy_road.grant(player, items)
        return trophy_road.DELIVERY_BOX[BOXES[kind]], items
    items = []
    if kind == R_GOLD:
        items = [(trophy_road.ITEM_GOLD, None, amount)]
    elif kind == R_GEMS:
        items = [(trophy_road.ITEM_GEMS, None, amount)]
    elif kind == R_POWER_POINTS:
        target = player.get('brawler', 0)
        items = [(trophy_road.ITEM_POWER_POINTS, target,
                  min(amount, brawlers.points_needed(player, target)) or amount)]
    elif kind == R_BRAWLER and extra in CHARACTERS:
        brawler = CHARACTERS[extra]
        items = ([(trophy_road.ITEM_POWER_POINTS, brawler, 100)] if brawler in brawlers.owned(player)
                 else [(trophy_road.ITEM_BRAWLER, brawler, 1)])
    trophy_road.grant(player, items)
    if kind in (R_SKIN, R_SKIN_ALT) and extra in SKINS:
        skins = player.setdefault('owned_skins', [])
        if SKINS[extra] not in skins:
            skins.append(SKINS[extra])
        return trophy_road.SINGLE_REWARD, [(ITEM_SKIN, SKINS[extra], 1)]
    return trophy_road.SINGLE_REWARD, items  # Pins are cosmetic and not tracked yet.


def claim(player, track, index):
    """Claim one tier. Returns (box, items) or None when it isn't claimable."""
    bp = state(player)
    table = FREE_TRACK if track == FREE else PREMIUM_TRACK if track == PREMIUM else None
    key = 'free' if track == FREE else 'paid'
    if table is None or not 0 <= index < len(table):
        return None
    if track == PREMIUM and not bp['premium']:
        return None
    needed, kind, amount, extra = table[index]
    if bp['tokens'] < needed or bp[key] & mask_bit(index):
        return None
    bp[key] |= mask_bit(index)
    return reward_items(player, kind, amount, extra)


def buy_pass(player):
    bp = state(player)
    if bp['premium'] or player.get('gems', 0) < PASS_PRICE:
        return False
    player['gems'] -= PASS_PRICE
    bp['premium'] = True
    return True


def buy_tier(player):
    """Raise tokens to the next tier threshold for TIER_PRICE gems."""
    bp = state(player)
    upcoming = [needed for needed, *_ in FREE_TRACK if needed > bp['tokens']]
    if not upcoming or player.get('gems', 0) < TIER_PRICE:
        return False
    player['gems'] -= TIER_PRICE
    bp['tokens'] = upcoming[0]
    return True


def encode(w, player):
    """The Brawl Pass block of home data."""
    bp = state(player)
    w.boolean(True)
    w.values(SEASON, bp['tokens'], int(bp['premium']), 0)
    for mask in (bp['paid'], bp['free']):
        w.vint(1)
        for word in range(4):
            value = (mask >> (32 * word)) & 0xFFFFFFFF
            w.integer(value - (1 << 32) if value >= 1 << 31 else value)
