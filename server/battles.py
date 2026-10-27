"""Bot-only match setup. Real-time bot simulation runs in the v29 client."""
from dataclasses import dataclass, field
import secrets
import time
import uuid

from protocol import Reader, Writer


@dataclass
class BotBattle:
    player_id: int
    brawler: int = 0
    map_id: int = 7
    match_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    seed: int = field(default_factory=lambda: secrets.randbelow(2**30))
    started_at: int = field(default_factory=lambda: int(time.time()))
    completed: bool = False
    participants: list = field(default_factory=list)

    @property
    def roster(self):
        return [self.brawler, 1, 2, 3, 4, 5]


def start_loading(player, battle):
    w = Writer()
    # Six participants, local player index zero, blue team zero.
    for value in [6, 0, 0, 6]:
        w.integer(value)
    for index, brawler in enumerate(battle.roster):
        human = index == 0
        w.long(player['id'] if human else 0)
        w.values(index, 0 if index < 3 else 1, 0)
        w.integer(0)
        w.reference(16, brawler)
        if human:
            w.reference(29, 0)
        else:
            w.vint(0)  # Default skin for the bot's character.
        w.boolean(False)
        w.boolean(False)
        w.string(player['name'] if human else 'Bot ' + str(index))
        w.values(1, 28000000 + (player['icon'] if human else 0),
                 43000000 + (player['name_color'] if human else 0), 0)
        w.boolean(not human)
    for value in [0, 0, battle.seed]:
        w.integer(value)
    w.values(0, 1, 1)
    w.boolean(True)
    w.values(0, 0)
    w.reference(15, battle.map_id)
    w.boolean(False)
    w.boolean(False)
    return w.bytes()


def read_result(payload, battle):
    r = Reader(payload)
    result, mode, rank = r.vint(), r.vint(), r.vint()
    table, map_id, players = r.vint(), r.vint(), r.vint()
    if result not in (0, 1, 2) or table != 15 or map_id != battle.map_id or players != 6:
        raise ValueError('invalid result for the active bot battle')
    participants = []
    for index in range(players):
        if r.vint() != 16:
            raise ValueError('invalid battle character reference')
        brawler = r.vint()
        skin_table = r.vint()
        if skin_table not in (0, 29):
            raise ValueError('invalid battle skin reference')
        skin = r.vint() if skin_table else None
        team, local = r.vint(), r.vint()
        name = r.string()
        if not 0 <= brawler <= 40 or local not in (0, 1) or team not in (0, 1):
            raise ValueError('invalid bot participant')
        if not name or len(name) > 40:
            raise ValueError('invalid bot participant name')
        participants.append({'brawler': brawler, 'skin': skin, 'local': bool(local),
                             'team': team, 'name': name if local else 'Bot ' + name})
    humans = [p for p in participants if p['local']]
    if len(humans) != 1 or humans[0]['brawler'] != battle.brawler:
        raise ValueError('result must contain exactly the active human character')
    if any(sum(p['team'] == team for p in participants) != 3 for team in (0, 1)):
        raise ValueError('bot battle requires two teams of three')
    if r.offset != len(payload):
        raise ValueError('trailing battle result data')
    battle.participants = participants
    return result


def battle_result(player, battle, result, progress):
    w = Writer()
    w.values(1, result, 0, progress['delta'], *([0] * 13))
    for flag in [False, False, False, False, True, False, False]:
        w.boolean(flag)
    w.vint(-1)  # No championship challenge; -64 resolves to invalid native data.
    w.boolean(False)
    w.vint(6)
    human_team = next(p['team'] for p in battle.participants if p['local'])
    for participant in battle.participants:
        brawler = participant['brawler']
        human = participant['local']
        # Three adjacent native boolean flags: local, opposing team, star player.
        w.boolean(human)
        w.boolean(participant['team'] != human_team)
        w.boolean(False)
        w.reference(16, brawler)
        if participant['skin'] is not None:
            w.reference(29, participant['skin'])
        else:
            w.vint(0)
        w.values(progress['old_trophies'] if human else 0, 0, 1)
        w.boolean(human)
        if human:
            w.long(player['id'])
        w.string(player['name'] if human else participant['name'])
        w.values(1, 28000000 + (player['icon'] if human else 0),
                 43000000 + (player['name_color'] if human else 0), 0)
    w.values(1, 0, progress['experience'])  # Experience reward entries.
    w.vint(0)  # Rank/level-up bonuses.
    w.values(2, 1, progress['old_trophies'], progress['old_trophies'],
             5, 220 + progress['old_experience'], 0)
    w.reference(28, player['icon'])
    w.boolean(False)  # Return home rather than network play-again matchmaking.
    return w.bytes()

