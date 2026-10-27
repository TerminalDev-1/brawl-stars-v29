"""Home-screen commands batched in EndClientTurn (14102).

Each command starts with its tick, a second tick and an executor ID, then a
body. The client applies most commands itself immediately (selecting a
brawler, upgrading, spending gems); the server repeats them so the change
persists. Box purchases also need the server to send the contents.
"""
from dataclasses import dataclass

import brawlers
import shop
import trophy_road
from protocol import Reader

SCID, VINT = 'scid', 'vint'

# Body layouts, captured from the v29 client on the tablet.
BODIES = {
    500: (VINT,),                    # Purchase shop box (box index).
    506: (SCID,),                    # Select skin.
    509: (),                         # Buy token doubler.
    515: (VINT, VINT, VINT, VINT),   # Shop opened / offers viewed.
    517: (VINT, VINT, VINT, VINT),   # Claim reward (track, ...).
    519: (VINT,),                    # Purchase daily offer (offer index).
    520: (SCID,),                    # Upgrade brawler.
    521: (VINT,),                    # Buy coins with gems (pack index).
    522: (SCID,),                    # Brawler seen (removes the "new" badge).
    525: (SCID,),                    # Select brawler.
}

# Shop box index -> (gem cost, box type). Matches the home data prices.
SHOP_BOXES = {1: (30, trophy_road.BIG_BOX), 3: (80, trophy_road.MEGA_BOX)}
TOKEN_DOUBLER = (40, 1500)  # gems, tokens doubled
COIN_PACKS = {0: (10, 1000)}  # pack index -> (gems, coins)


@dataclass
class Command:
    kind: int
    fields: list


def read_scid(r):
    table = r.vint()
    return (table, r.vint()) if table else (0, None)


def parse(payload):
    """Returns (commands, first unknown command ID or None)."""
    r = Reader(payload)
    r.vint()
    r.vint(), r.vint()  # Tick and checksum.
    commands = []
    for _ in range(r.vint()):
        kind = r.vint()
        if kind not in BODIES:
            return commands, kind
        r.vint(), r.vint(), r.vint(), r.vint()  # Ticks and executor.
        fields = [read_scid(r) if field == SCID else r.vint() for field in BODIES[kind]]
        commands.append(Command(kind, fields))
    return commands, None


class Result:
    def __init__(self):
        self.changed = False
        self.replies = []  # (message type, payload)
        self.notes = []
        self.resync = False
        self.skin = None  # Skin selected in this batch; it belongs to the brawler selected with it.


def finish(player, result):
    """Apply batch-level effects once every command in the batch has run."""
    if result.skin is not None:
        player.setdefault('skins', {})[str(player.get('brawler', 0))] = result.skin
        result.changed = True


def spend_gems(player, cost, result, what):
    if player.get('gems', 0) < cost:
        result.notes.append(f'not enough gems for {what}')
        result.resync = True
        return False
    player['gems'] -= cost
    result.changed = True
    return True


def apply(player, command, result):
    kind, fields = command.kind, command.fields
    if kind == 517:
        track = fields[0]
        if track != 6:
            result.notes.append(f'claim ignored track={track}')
            return
        claimed = trophy_road.claim(player)
        if claimed is None:
            result.notes.append('trophy road not claimable')
            result.resync = True
            return
        index, box, items = claimed
        result.changed = True
        result.notes.append(f'trophy road milestone={index} box={box} items={items}')
        result.replies.append((24111, trophy_road.delivery_command(box, items, track, index + 2)))
    elif kind == 525:
        table, brawler = fields[0]
        if table == 16 and brawler in brawlers.owned(player):
            player['brawler'] = brawler
            result.changed = True
            result.notes.append(f'select brawler={brawler}')
    elif kind == 506:
        table, skin = fields[0]
        if table == 29:
            result.skin = skin
            result.notes.append(f'select skin={skin}')
    elif kind == 522:
        table, brawler = fields[0]
        seen = player.setdefault('seen', [])
        if table == 16 and brawler not in seen:
            seen.append(brawler)
            result.changed = True
    elif kind == 520:
        table, brawler = fields[0]
        level = brawlers.upgrade(player, brawler) if table == 16 else None
        if level is None:
            result.notes.append(f'upgrade refused brawler={brawler}')
            result.resync = True
        else:
            result.changed = True
            result.notes.append(f'upgrade brawler={brawler} power={level + 1}')
    elif kind == 500:
        index = fields[0]
        if index not in SHOP_BOXES:
            result.notes.append(f'unknown shop box={index}')
            result.resync = True
            return
        cost, box = SHOP_BOXES[index]
        if not spend_gems(player, cost, result, f'box {index}'):
            return
        items = trophy_road.box_items(player, box)
        trophy_road.grant(player, items)
        result.changed = True
        result.notes.append(f'buy box={index} gems={cost} items={items}')
        result.replies.append((24111, trophy_road.delivery_command(trophy_road.DELIVERY_BOX[box], items)))
    elif kind == 509:
        cost, amount = TOKEN_DOUBLER
        if not spend_gems(player, cost, result, 'token doubler'):
            return
        player['token_doubler'] = player.get('token_doubler', 0) + amount
        result.notes.append(f'buy token doubler gems={cost}')
    elif kind == 521:
        if fields[0] not in COIN_PACKS:
            result.notes.append(f'unknown coin pack={fields[0]}')
            result.resync = True
            return
        cost, coins = COIN_PACKS[fields[0]]
        if not spend_gems(player, cost, result, 'coin pack'):
            return
        player['gold'] = player.get('gold', 0) + coins
        result.notes.append(f'buy coins={coins} gems={cost}')
    elif kind == 519:
        items = shop.buy(player, fields[0])
        if items is None:
            result.notes.append(f'offer {fields[0]} refused')
            result.resync = True
            return
        result.changed = True
        result.notes.append(f'buy offer={fields[0]} items={items}')
        result.replies.append((24111, trophy_road.delivery_command(trophy_road.SINGLE_REWARD, items)))
    elif kind == 515:
        pass  # Viewing the shop changes nothing on the server.
    else:
        result.notes.append(f'command={kind} fields={fields} not handled yet')
