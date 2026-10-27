"""Transactional SQLite accounts with an atomic JSON recovery snapshot."""
import hashlib
from contextlib import contextmanager
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path


class AccountStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'players.sqlite3'
        self.backup_path = self.directory / 'players.json'
        self.lock = threading.RLock()
        fresh = not self.path.exists()
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS players '
                       '(id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash TEXT NOT NULL, '
                       'state TEXT NOT NULL, created_at INTEGER NOT NULL, '
                       'last_login INTEGER NOT NULL, logins INTEGER NOT NULL)')
            if fresh and self.backup_path.exists():
                snapshot = json.loads(self.backup_path.read_text(encoding='utf-8'))
                for row in snapshot['players']:
                    db.execute('INSERT INTO players VALUES (?,?,?,?,?,?)',
                               (row['id'], row['token_hash'], json.dumps(row['state']),
                                row['created_at'], row['last_login'], row['logins']))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def login(self, player_id, token):
        with self.lock, self.connect() as db:
            now = int(time.time())
            if player_id:
                row = db.execute('SELECT * FROM players WHERE id=?', (player_id,)).fetchone()
                if row is None or not token or not hmac.compare_digest(row['token_hash'], self.digest(token)):
                    raise PermissionError('Unknown account or invalid token')
                state = json.loads(row['state'])
            else:
                token = secrets.token_urlsafe(32)
                state = {'name': 'Player', 'gems': 100, 'gold': 1000, 'trophies': 0,
                         'icon': 0, 'name_color': 0, 'brawler': 0, 'theme': 0}
                cursor = db.execute('INSERT INTO players(token_hash,state,created_at,last_login,logins) '
                                    'VALUES(?,?,?,?,0)', (self.digest(token), json.dumps(state), now, now))
                player_id = cursor.lastrowid
            db.execute('UPDATE players SET last_login=?, logins=logins+1 WHERE id=?', (now, player_id))
            db.commit()
            self.backup()
            state['id'] = player_id
            return state, token

    def save(self, state):
        with self.lock, self.connect() as db:
            values = {key: value for key, value in state.items() if key != 'id'}
            db.execute('UPDATE players SET state=? WHERE id=?', (json.dumps(values), state['id']))
            db.commit()
            self.backup()

    def backup(self):
        with self.lock, self.connect() as db:
            records = []
            for row in db.execute('SELECT * FROM players ORDER BY id'):
                record = dict(row)
                record['state'] = json.loads(record['state'])
                records.append(record)
            temp = self.backup_path.with_suffix('.json.tmp')
            with temp.open('w', encoding='utf-8') as output:
                json.dump({'schema': 1, 'players': records}, output, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp, self.backup_path)
