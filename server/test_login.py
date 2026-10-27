"""Run: python -m unittest discover -s server -p test_login.py -v."""
import json
import shutil
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from app import Server
from protocol import Reader, Writer, packet, recv_exact
from storage import AccountStore


def receive(sock):
    header = recv_exact(sock, 7)
    return int.from_bytes(header[:2], 'big'), recv_exact(sock, int.from_bytes(header[2:5], 'big'))


def login_payload(account=0, token=None):
    w = Writer()
    w.long(account)
    w.string(token)
    for value in [29, 1, 270]:
        w.integer(value)
    return w.bytes()


class LoginTests(unittest.TestCase):
    def test_theme_migration_preserves_account_and_custom_theme(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            player, token = store.login(0, None)
            custom, custom_token = store.login(0, None)
            self.assertEqual(player['theme'], 15)
            player['theme'] = 0
            custom['theme'] = 8
            store.save(player)
            store.save(custom)
            with store.connect() as db:
                db.execute('PRAGMA user_version=0')
            migrated = AccountStore(temp)
            loaded, _ = migrated.login(player['id'], token)
            self.assertEqual(loaded['theme'], 15)
            self.assertEqual(loaded['gold'], player['gold'])
            other, _ = migrated.login(custom['id'], custom_token)
            self.assertEqual(other['theme'], 8)
            loaded['theme'] = 0
            migrated.save(loaded)
            unchanged, _ = AccountStore(temp).login(player['id'], token)
            self.assertEqual(unchanged['theme'], 0)

    def test_native_wire_fixtures(self):
        for value, encoded in [(0, '00'), (63, '3f'), (64, '8001'),
                               (-1, '7f'), (-64, '40'), (-65, 'ff7e')]:
            w = Writer()
            w.vint(value)
            self.assertEqual(w.bytes().hex(), encoded)
        w = Writer()
        w.boolean(True)
        w.boolean(True)
        w.boolean(False)
        w.vint(0)
        w.boolean(True)
        self.assertEqual(w.bytes(), b'\x03\x00\x01')

    def test_variable_integer_boundaries(self):
        for value in [0, 1, -1, 63, 64, -64, 127, 128, -128, 16384, 2**31 - 1, -2**31]:
            with self.subTest(value=value):
                w = Writer()
                w.vint(value)
                self.assertEqual(Reader(w.bytes()).vint(), value)

    def test_storage_json_recovery_and_authentication(self):
        with tempfile.TemporaryDirectory() as temp:
            store = AccountStore(Path(temp) / 'primary')
            player, token = store.login(0, None)
            player['name'] = 'Test Player'
            store.save(player)
            with self.assertRaises(PermissionError):
                store.login(player['id'], 'invalid-token')
            recovered_dir = Path(temp) / 'recovery'
            recovered_dir.mkdir()
            shutil.copyfile(store.backup_path, recovered_dir / 'players.json')
            recovered = AccountStore(recovered_dir)
            loaded, returned_token = recovered.login(player['id'], token)
            self.assertEqual(loaded['name'], 'Test Player')
            self.assertEqual(returned_token, token)
            self.assertNotIn(token, store.backup_path.read_text())

    def test_fragmented_login_reconnect_keepalive_and_parallel_clients(self):
        with tempfile.TemporaryDirectory() as temp:
            server = Server(('127.0.0.1', 0), AccountStore(temp))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                # An idle connection must not stop a second client logging in.
                with socket.create_connection(server.server_address, timeout=3) as idle:
                    with socket.create_connection(server.server_address, timeout=3) as client:
                        frame = packet(10101, login_payload(), 10)
                        for byte in frame:
                            client.sendall(bytes([byte]))
                        kind, data = receive(client)
                        self.assertEqual(kind, 20104)
                        reader = Reader(data)
                        self.assertEqual(reader.integer(), 0)
                        account = reader.integer()
                        reader.take(8)
                        token = reader.string()
                        self.assertEqual([receive(client)[0] for _ in range(3)], [24101, 20105, 24399])
                        client.sendall(packet(10108))
                        self.assertEqual(receive(client), (20108, b''))
                    with socket.create_connection(server.server_address, timeout=3) as client:
                        client.sendall(packet(10101, login_payload(account, token), 10))
                        self.assertEqual(receive(client)[0], 20104)
                        self.assertEqual([receive(client)[0] for _ in range(3)], [24101, 20105, 24399])
                snapshot = json.loads((Path(temp) / 'players.json').read_text())
                self.assertEqual(len(snapshot['players']), 1)
                self.assertEqual(snapshot['players'][0]['logins'], 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
