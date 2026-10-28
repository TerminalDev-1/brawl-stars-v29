"""/dev commands in team chat, and the team messages that carry them."""
import unittest

import brawlers
import devcommands
import team
from protocol import Reader


def player(**extra):
    p = {'id': 2, 'name': 'Player', 'gems': 0, 'gold': 0, 'trophies': 100, 'highest_trophies': 100,
         'icon': 0, 'name_color': 0, 'brawler': 39, 'theme': 15, 'unlocked': [0, 39],
         'brawler_trophies': {'0': 0, '39': 100}}
    p.update(extra)
    return p


class DevCommandTests(unittest.TestCase):
    def test_plain_chat_is_not_a_command(self):
        self.assertIsNone(devcommands.run(player(), 'hello'))

    def test_gems_and_coins(self):
        p = player()
        result = devcommands.run(p, '/gems 500')
        self.assertEqual((p['gems'], result.changed), (500, True))
        result = devcommands.run(p, '/coins 5000')
        self.assertEqual((p['gold'], result.changed), (5000, True))

    def test_total_and_brawler_trophies(self):
        p = player()
        devcommands.run(p, '/t 0')
        self.assertEqual((p['trophies'], p['highest_trophies']), (0, 0))
        devcommands.run(p, '/bt 750')
        self.assertEqual(p['brawler_trophies']['39'], 750)
        self.assertEqual(p['trophies'], 0)  # /bt leaves the total alone.

    def test_setw_changes_win_and_showdown_rewards(self):
        import tempfile
        from battles import BotBattle
        from storage import AccountStore
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            p, _ = store.login(0, None)
            devcommands.run(p, '/setw 14')
            store.save(p)
            for result, rank, expected in [(0, 0, 14), (1, 1, 14), (2, 2, 11), (6, 6, -8)]:
                battle = BotBattle(p['id'])
                store.begin_battle(p['id'], battle.match_id, 13 if rank else 7, battle.started_at)
                reward = store.complete_battle(p['id'], battle.match_id, result, 0, rank)
                self.assertEqual(reward['delta'], expected)

    def test_unlock_and_max_by_name(self):
        p = player()
        devcommands.run(p, '/unlock el primo')
        self.assertIn(10, p['unlocked'])
        devcommands.run(p, '/max mr. p')
        self.assertTrue(brawlers.maxed(p, 31))
        devcommands.run(p, '/max all')
        self.assertTrue(all(brawlers.maxed(p, b) for b in brawlers.NAMES))

    def test_bad_input_changes_nothing(self):
        p = player()
        for text in ('/gems lots', '/t -5', '/unlock nobody', '/fly'):
            self.assertFalse(devcommands.run(p, text).changed)
        self.assertEqual(p['gems'], 0)


class TeamMessageTests(unittest.TestCase):
    def test_create_payload_from_the_tablet(self):
        self.assertEqual(team.read_create(bytes.fromhex('7f7f0000')), (0, 0))

    def test_chat_payload_from_the_tablet(self):
        self.assertEqual(team.read_chat(bytes.fromhex('000000092f67656d7320353030')), '/gems 500')

    def test_chat_entry_carries_sender_and_text(self):
        room = team.Room(0, 7)
        r = Reader(team.chat_entry(room, 0, 'Server', 'Gems set to 500.'))
        self.assertEqual([r.vint() for _ in range(8)], [0, room.id, 1, 2, 0, 1, 0, 0])
        self.assertEqual(r.string(), 'Server')
        self.assertEqual([r.vint() for _ in range(3)], [0, 0, 0])
        self.assertEqual(r.string(), 'Gems set to 500.')


if __name__ == '__main__':
    unittest.main()
