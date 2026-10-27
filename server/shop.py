"""Daily shop offers: generated once per day per player, bought with coins."""
import datetime
import random

import brawlers
import trophy_road

OFFER_BRAWLER = 3        # Shop item type: unlock a brawler.
OFFER_POWER_POINTS = 8   # Shop item type: power points for one brawler.
SECTION_SPECIAL, SECTION_DAILY = 0, 1
COLETTE = 39
CURRENCY_GEMS, CURRENCY_GOLD = 0, 1
POINT_PRICE = 2           # Coins per power point, as in v29 daily deals.
OFFER_SECONDS = 86400


def today():
    return datetime.date.today().isoformat()


def seconds_left():
    now = datetime.datetime.now()
    tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
    return int((tomorrow - now).total_seconds())


def free_colette(player):
    """Colette is free in the shop until the player owns her."""
    offers = player['offers']
    if COLETTE in brawlers.owned(player) or any(o['type'] == OFFER_BRAWLER for o in offers['items']):
        return False
    offers['items'].append({'type': OFFER_BRAWLER, 'amount': 1, 'brawler': COLETTE,
                            'currency': CURRENCY_GEMS, 'cost': 0, 'section': SECTION_SPECIAL})
    return True


def daily_offers(player):
    """Refresh the player's offers when the day changes. Returns True if state changed."""
    current = player.get('offers')
    if current and current.get('day') == today():
        return free_colette(player)
    rng = random.Random(f"{player['id']}-{today()}")
    hungry = [b for b in brawlers.owned(player) if brawlers.points_needed(player, b) > 0]
    rng.shuffle(hungry)
    items = []
    for brawler in hungry[:3]:
        amount = min(rng.choice((10, 15, 25, 40, 55, 70)), brawlers.points_needed(player, brawler))
        items.append({'type': OFFER_POWER_POINTS, 'amount': amount, 'brawler': brawler,
                      'currency': CURRENCY_GOLD, 'cost': amount * POINT_PRICE})
    player['offers'] = {'day': today(), 'items': items, 'bought': []}
    free_colette(player)
    return True


def _byte_flag(w, value):
    """A boolean stored in its own byte, as the reference v29 server writes offers."""
    w.bit_index = None
    w.data.append(1 if value else 0)


def encode_offers(w, player):
    offers = player.get('offers') or {'items': [], 'bought': []}
    w.vint(len(offers['items']))
    for index, offer in enumerate(offers['items']):
        w.vint(1)  # One item in this offer.
        w.values(offer['type'], offer['amount'])
        w.reference(16, offer['brawler'])
        w.vint(0)  # Skin / extra data.
        w.values(offer['currency'], offer['cost'], seconds_left(), 2, 100)  # 2 = already viewed
        _byte_flag(w, index in offers['bought'])
        _byte_flag(w, False)
        special = offer.get('section', SECTION_DAILY) == SECTION_SPECIAL
        w.vint(SECTION_SPECIAL if special else SECTION_DAILY)
        _byte_flag(w, False)  # No crossed-out old price.
        w.vint(0)
        w.integer(0)
        title = b'FREE COLETTE!' if special else b'daily'
        w.data.extend(bytes(2))  # Title as a native string reference.
        w.vint(len(title))
        w.data.extend(title)
        _byte_flag(w, False)
        w.string('offer_gems')
        w.vint(0)
        _byte_flag(w, False)
        w.values(0, 0)


def buy(player, index):
    """Apply a daily offer purchase. Returns delivery items or None if refused."""
    offers = player.get('offers') or {}
    items = offers.get('items', [])
    if not 0 <= index < len(items) or index in offers.get('bought', []):
        return None
    offer = items[index]
    balance = 'gold' if offer['currency'] == CURRENCY_GOLD else 'gems'
    if player.get(balance, 0) < offer['cost']:
        return None
    player[balance] -= offer['cost']
    offers['bought'].append(index)
    if offer['type'] == OFFER_BRAWLER:
        if offer['brawler'] in brawlers.owned(player):
            return None
        delivered = [(trophy_road.ITEM_BRAWLER, offer['brawler'], 1)]
    else:
        delivered = [(trophy_road.ITEM_POWER_POINTS, offer['brawler'], offer['amount'])]
    trophy_road.grant(player, delivered)
    return delivered
