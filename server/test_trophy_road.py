"""Trophy Road claims, delivery encoding, home data, and Showdown results."""
import json
import socket
import tempfile
import threading
import unittest

from app import Server
from battles import BotBattle, battle_result, read_result
from messages import home_data
from protocol import Reader, Writer, packet
from storage import AccountStore
from test_login import login_payload, receive
import trophy_road

# Native claim captured on the tablet: EndClientTurn with command 517, track 6.
NATIVE_CLAIM = bytes.fromhex('00950400018508940494047f7f06000000ffffffff')


def player(trophies):
    return {'id': 1, 'name': 'Player', 'gems': 100, 'gold': 1000, 'trophies': trophies,
            'highest_trophies': trophies, 'icon': 0, 'name_color': 0, 'brawler': 0, 'theme': 15}


class TrophyRoadTests(unittest.TestCase):
    def setUp(self):
        # Box brawler drops are random; keep these tests deterministic.
        self.drop = trophy_road._new_brawler
        trophy_road._new_brawler = lambda player, scale: None

    def tearDown(self):
        trophy_road._new_brawler = self.drop

    def test_claims_follow_the_v29_road_in_order(self):
        p = player(24)
        index, box, items = trophy_road.claim(p)
        self.assertEqual((index, box), (0, 10))  # Brawl Box at 5 trophies.
        self.assertEqual(p['gold'], 1000 + items[0][2])
        self.assertEqual(trophy_road.claim(p)[1:], (100, [(1, 8, 1)]))  # Nita at 10.
        self.assertEqual(p['unlocked'], [0, 8])
        self.assertEqual(trophy_road.claim(p)[1], 10)  # Brawl Box at 20.
        self.assertIsNone(trophy_road.claim(p))  # Showdown unlock needs 30.
        self.assertEqual(p['trophy_road'], 4)

    def test_unlock_steps_deliver_nothing_and_gold_steps_pay(self):
        p = player(600)
        p['trophy_road'] = 4
        self.assertEqual(trophy_road.claim(p)[1:], (100, []))
        p['trophy_road'] = 16
        gold = p['gold']
        self.assertEqual(trophy_road.claim(p)[2], [(7, None, 50)])
        self.assertEqual(p['gold'], gold + 50)

    def test_delivery_encoding_matches_native_layout(self):
        payload = trophy_road.delivery_command(100, [(1, 8, 1)], 6, 3)
        r = Reader(payload)
        self.assertEqual([r.vint() for _ in range(7)], [203, 0, 1, 100, 1, 1, 16])
        self.assertEqual([r.vint() for _ in range(6)], [8, 1, 0, 0, 0, 0])
        self.assertEqual(r.take(1), b'\x00')
        self.assertEqual([r.vint() for _ in range(4)], [6, 3, 0, 1])
        self.assertEqual(r.offset, len(payload))

    def test_home_data_lists_unlocked_brawlers(self):
        p = player(35)
        p.update(unlocked=[0, 8], power_points={'0': 18}, trophy_road=5)
        self.assertGreater(len(home_data(p)), len(home_data(player(35))))

    def test_claim_over_tcp_persists(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            server = Server(('127.0.0.1', 0), store)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with socket.create_connection(server.server_address, timeout=3) as client:
                    client.sendall(packet(10101, login_payload()))
                    for kind in [20104, 24101, 20105, 24399]:
                        self.assertEqual(receive(client)[0], kind)
                    client.sendall(packet(14102, NATIVE_CLAIM))
                    self.assertEqual(receive(client)[0], 24101)  # Not claimable at 0: resync.
                with store.connect() as db:
                    state = json.loads(db.execute('SELECT state FROM players').fetchone()[0])
                self.assertEqual(state.get('trophy_road', 1), 1)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


def showdown_result(rank, players=10, result=None):
    w = Writer()
    w.values(rank if result is None else result, 0, rank, 15, 13, players)
    for index in range(players):
        w.values(16, 0 if index == 0 else index, 0, index, int(index == 0))
        w.string('Player' if index == 0 else str(index))
    return w.bytes()


class ShowdownTests(unittest.TestCase):
    def test_showdown_result_reports_placement(self):
        battle = BotBattle(1)
        read_result(showdown_result(3), battle)
        self.assertTrue(battle.showdown)
        self.assertEqual((battle.map_id, battle.rank, len(battle.participants)), (13, 3, 10))
        payload = battle_result({'id': 1, 'name': 'Player', 'icon': 0, 'name_color': 0}, battle, 1,
                                {'delta': 7, 'old_trophies': 0, 'experience': 20, 'old_experience': 0})
        self.assertEqual([Reader(payload).vint() for _ in range(1)], [2])

    def test_showdown_low_placement_is_accepted(self):
        # Captured case: 7th place arrives as result=7, rank=7.
        battle = BotBattle(1)
        self.assertEqual(read_result(showdown_result(7), battle), 7)
        self.assertEqual(battle.rank, 7)

    def test_showdown_rejects_bad_rank_and_unowned_brawler(self):
        with self.assertRaises(ValueError):
            read_result(showdown_result(11), BotBattle(1))
        with self.assertRaises(ValueError):
            read_result(showdown_result(1), BotBattle(1, owned=(8,)))

    def test_showdown_trophies_by_rank_without_losses(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            p, _ = store.login(0, None)
            for rank, expected in [(1, 250), (4, 100), (10, -25)]:
                battle = BotBattle(p['id'])
                store.begin_battle(p['id'], battle.match_id, 13, battle.started_at)
                reward = store.complete_battle(p['id'], battle.match_id, rank, 0, rank)
                self.assertEqual(reward['delta'], expected)
            self.assertEqual(reward['player']['trophies'], 325)
            self.assertEqual(reward['player']['brawler_trophies'], {'0': 325})
            self.assertEqual(reward['player']['highest_trophies'], 350)
            # A loss can't push a brawler below zero.
            battle = BotBattle(p['id'], 8)
            store.begin_battle(p['id'], battle.match_id, 13, battle.started_at)
            reward = store.complete_battle(p['id'], battle.match_id, 9, 8, 9)
            self.assertEqual(reward['delta'], 0)
            self.assertEqual(reward['player']['brawler_trophies']['8'], 0)


if __name__ == '__main__':
    unittest.main()
