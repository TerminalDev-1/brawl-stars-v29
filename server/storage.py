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

DEFAULT_THEME = 15  # v29: Welcome to Starr Park / Gift Shop.


class AccountStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'players.sqlite3'
        self.backup_path = self.directory / 'players.json'
        self.lock = threading.RLock()
        fresh = not self.path.exists()
        migrated = False
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS players '
                       '(id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash TEXT NOT NULL, '
                       'state TEXT NOT NULL, created_at INTEGER NOT NULL, '
                       'last_login INTEGER NOT NULL, logins INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS bot_battles '
                       '(match_id TEXT PRIMARY KEY, player_id INTEGER NOT NULL, '
                       'map_id INTEGER NOT NULL, started_at INTEGER NOT NULL, '
                       'finished_at INTEGER, result INTEGER, trophies_delta INTEGER NOT NULL DEFAULT 0)')
            if fresh and self.backup_path.exists():
                snapshot = json.loads(self.backup_path.read_text(encoding='utf-8'))
                for row in snapshot['players']:
                    db.execute('INSERT INTO players VALUES (?,?,?,?,?,?)',
                               (row['id'], row['token_hash'], json.dumps(row['state']),
                                row['created_at'], row['last_login'], row['logins']))
                for row in snapshot.get('bot_battles', []):
                    db.execute('INSERT INTO bot_battles VALUES (?,?,?,?,?,?,?)',
                               tuple(row[key] for key in ['match_id', 'player_id', 'map_id',
                                     'started_at', 'finished_at', 'result', 'trophies_delta']))
                if snapshot.get('storage_version', 0) >= 1:
                    db.execute('PRAGMA user_version=1')
            if db.execute('PRAGMA user_version').fetchone()[0] < 1:
                for row in db.execute('SELECT id,state FROM players').fetchall():
                    state = json.loads(row['state'])
                    if state.get('theme', 0) == 0:
                        state['theme'] = DEFAULT_THEME
                        db.execute('UPDATE players SET state=? WHERE id=?',
                                   (json.dumps(state), row['id']))
                        migrated = True
                db.execute('PRAGMA user_version=1')
        if migrated:
            self.backup()

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
                         'icon': 0, 'name_color': 0, 'brawler': 0, 'theme': DEFAULT_THEME}
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

    def begin_battle(self, player_id, match_id, map_id, started_at):
        with self.lock, self.connect() as db:
            db.execute('INSERT INTO bot_battles(match_id,player_id,map_id,started_at) VALUES(?,?,?,?)',
                       (match_id, player_id, map_id, started_at))
            db.commit()
            self.backup()

    def complete_battle(self, player_id, match_id, result):
        if result not in (0, 1, 2):
            raise ValueError('invalid bot battle result')
        with self.lock, self.connect() as db:
            match = db.execute('SELECT * FROM bot_battles WHERE match_id=? AND player_id=?',
                               (match_id, player_id)).fetchone()
            if match is None:
                raise ValueError('unknown bot battle')
            if match['finished_at'] is not None:
                return None
            row = db.execute('SELECT state FROM players WHERE id=?', (player_id,)).fetchone()
            state = json.loads(row['state'])
            old_trophies = state['trophies']
            old_experience = state.get('experience', 0)
            delta = 8 if result == 0 else 0
            experience = 20 if result == 0 else 10
            state['trophies'] += delta
            state['highest_trophies'] = max(state.get('highest_trophies', 0), state['trophies'])
            state['experience'] = old_experience + experience
            state['battles_played'] = state.get('battles_played', 0) + 1
            state['bot_wins'] = state.get('bot_wins', 0) + int(result == 0)
            db.execute('UPDATE players SET state=? WHERE id=?', (json.dumps(state), player_id))
            db.execute('UPDATE bot_battles SET finished_at=?, result=?, trophies_delta=? WHERE match_id=?',
                       (int(time.time()), result, delta, match_id))
            db.commit()
            self.backup()
            state['id'] = player_id
            return {'player': state, 'delta': delta, 'experience': experience,
                    'old_trophies': old_trophies, 'old_experience': old_experience}

    def abandon_battle(self, player_id, match_id):
        with self.lock, self.connect() as db:
            db.execute('UPDATE bot_battles SET finished_at=?,result=-1 '
                       'WHERE match_id=? AND player_id=? AND finished_at IS NULL',
                       (int(time.time()), match_id, player_id))
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
                json.dump({'schema': 2, 'storage_version': db.execute('PRAGMA user_version').fetchone()[0],
                           'players': records,
                           'bot_battles': [dict(row) for row in db.execute('SELECT * FROM bot_battles ORDER BY started_at,match_id')]},
                          output, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp, self.backup_path)
