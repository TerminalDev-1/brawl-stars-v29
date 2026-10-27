"""Bot match lifecycle and persistent progression tests."""
import json
import shutil
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from app import Server
from battles import BotBattle, battle_result, read_result
from protocol import Reader, Writer, packet
from storage import AccountStore
from test_login import login_payload, receive


NATIVE_RESULT = bytes.fromhex(
    '0001000f070610001d00010100000006506c6179657210010000000000000131'
    '10100000000000000132100500000000000001331020000100000000013410050001000000000135')


class BattleTests(unittest.TestCase):
    def test_rewards_are_atomic_once_and_recoverable(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            player, token = store.login(0, None)
            battle = BotBattle(player['id'])
            store.begin_battle(player['id'], battle.match_id, 7, battle.started_at)
            reward = store.complete_battle(player['id'], battle.match_id, 0)
            self.assertEqual(reward['player']['trophies'], 500)
            self.assertEqual(reward['player']['experience'], 20)
            self.assertIsNone(store.complete_battle(player['id'], battle.match_id, 0))
            snapshot = json.loads(store.backup_path.read_text())
            self.assertEqual(snapshot['bot_battles'][0]['trophies_delta'], 500)
            recovered_dir = Path(temp) / 'recovered'
            recovered_dir.mkdir()
            shutil.copy(store.backup_path, recovered_dir / 'players.json')
            recovered = AccountStore(recovered_dir)
            restored, _ = recovered.login(player['id'], token)
            self.assertEqual(restored['battles_played'], 1)
            self.assertEqual(restored['trophies'], 500)
            self.assertIsNone(recovered.complete_battle(player['id'], battle.match_id, 0))

    def test_loss_and_draw_award_experience_without_trophy_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            player, _ = store.login(0, None)
            for result in (1, 2):
                battle = BotBattle(player['id'])
                store.begin_battle(player['id'], battle.match_id, 7, battle.started_at)
                reward = store.complete_battle(player['id'], battle.match_id, result)
                self.assertEqual(reward['delta'], 0)
                self.assertEqual(reward['experience'], 10)
            self.assertEqual(reward['player']['experience'], 20)
            self.assertEqual(reward['player']['bot_wins'], 0)
            self.assertEqual(reward['player']['battles_played'], 2)

    def test_abandoned_and_foreign_matches_cannot_award_rewards(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            player, token = store.login(0, None)
            other, _ = store.login(0, None)
            battle = BotBattle(player['id'])
            store.begin_battle(player['id'], battle.match_id, 7, battle.started_at)
            with self.assertRaises(ValueError):
                store.complete_battle(other['id'], battle.match_id, 0)
            store.abandon_battle(player['id'], battle.match_id)
            self.assertIsNone(store.complete_battle(player['id'], battle.match_id, 0))
            restored, _ = store.login(player['id'], token)
            self.assertEqual(restored['trophies'], 0)

    def test_result_must_match_map_and_participant_count(self):
        battle = BotBattle(1)
        for values in [(0, 1, 0, 15, 7, 6), (0, 1, 0, 15, 12, 6),
                       (0, 1, 0, 15, 7, 10), (4, 1, 0, 15, 7, 6)]:
            writer = Writer()
            writer.values(*values)
            if values == (0, 1, 0, 15, 7, 6):
                self.assertEqual(read_result(writer.bytes() + NATIVE_RESULT[6:], battle), 0)
            else:
                with self.assertRaises(ValueError):
                    read_result(writer.bytes() + NATIVE_RESULT[6:], battle)

    def test_native_result_uses_no_championship_and_actual_teams(self):
        battle = BotBattle(1)
        read_result(NATIVE_RESULT, battle)
        self.assertEqual([p['brawler'] for p in battle.participants], [0, 1, 16, 5, 32, 5])
        self.assertEqual([p['team'] for p in battle.participants], [1, 0, 0, 0, 1, 1])
        payload = battle_result({'id': 1, 'name': 'Player', 'icon': 0, 'name_color': 0},
                                battle, 0, {'delta': 8, 'old_trophies': 0,
                                            'experience': 20, 'old_experience': 0})
        reader = Reader(payload)
        self.assertEqual([reader.vint() for _ in range(4)], [1, 0, 0, 8])
        for _ in range(13):
            self.assertEqual(reader.vint(), 0)
        self.assertEqual(reader.take(1), b'\x10')  # Seven packed match flags.
        self.assertEqual(reader.vint(), -1)  # Native absence sentinel, not -64.
        self.assertEqual(reader.take(1), b'\x00')
        self.assertEqual(reader.vint(), 6)
        self.assertEqual(reader.take(1), b'\x01')  # Local blue player.

    def test_bot_start_result_duplicate_and_return_home_over_tcp(self):
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
                    client.sendall(packet(14103))
                    writer = Writer()
                    writer.values(0, 1, 0, 15, 7, 6)
                    client.sendall(packet(14110, writer.bytes() + NATIVE_RESULT[6:]))
                    self.assertEqual(receive(client)[0], 23456)
                    client.sendall(packet(14110, writer.bytes() + NATIVE_RESULT[6:]) + packet(14109))
                    self.assertEqual(receive(client)[0], 24101)
                    with store.connect() as db:
                        state = json.loads(db.execute('SELECT state FROM players').fetchone()[0])
                    self.assertEqual(state['battles_played'], 1)
                    self.assertEqual(state['trophies'], 500)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
