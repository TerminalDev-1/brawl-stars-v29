"""Threaded v29 login server with durable accounts and diagnostic logging."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import socket
import socketserver
import uuid

from messages import home_data, login_ok
from protocol import MAX_PACKET, Reader, Writer, packet, recv_exact
from storage import AccountStore

ROOT = Path(__file__).resolve().parent.parent
LOG = logging.getLogger('v29')


class Client(socketserver.BaseRequestHandler):
    def setup(self):
        self.player = None
        self.session = uuid.uuid4().hex[:8]
        self.request.settimeout(120)
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        LOG.info('session=%s CONNECT peer=%s', self.session, self.client_address[0])

    def send(self, kind, body=b'', version=0):
        self.request.sendall(packet(kind, body, version))
        LOG.debug('session=%s SEND type=%d length=%d version=%d', self.session, kind, len(body), version)

    def home(self):
        self.send(24101, home_data(self.player))

    def login(self, payload):
        if self.player is not None:
            raise ValueError('duplicate Login')
        r = Reader(payload)
        high, low, token = r.integer(), r.integer(), r.string()
        major, minor, build = r.integer(), r.integer(), r.integer()
        if high != 0 or low < 0 or major != 29:
            raise ValueError('unsupported account ID or client version')
        LOG.info('session=%s LOGIN requested_id=%d client=%d.%d.%d',
                 self.session, low, major, minor, build)
        self.player, token = self.server.store.login(low, token)
        LOG.info('session=%s LOGIN_OK player=%d log_file=debuglog.txt', self.session, self.player['id'])
        self.send(20104, login_ok(self.player, token), version=1)
        self.home()
        friends = Writer()
        friends.integer(0)
        friends.boolean(True)
        friends.integer(0)
        self.send(20105, friends.bytes())
        self.send(24399, b'\x00\x00')

    def handle(self):
        try:
            while True:
                header = recv_exact(self.request, 7)
                kind = int.from_bytes(header[:2], 'big')
                size = int.from_bytes(header[2:5], 'big')
                version = int.from_bytes(header[5:], 'big')
                if size > MAX_PACKET:
                    raise ValueError('packet exceeds limit')
                payload = recv_exact(self.request, size)
                LOG.debug('session=%s RECV type=%d length=%d version=%d', self.session, kind, size, version)
                if kind == 10100:
                    raise ValueError('client requires the raw messaging hook')
                elif kind == 10101:
                    self.login(payload)
                elif self.player is None:
                    raise ValueError('login required')
                elif kind == 10108:
                    self.send(20108)
                elif kind in (14101, 14109):
                    self.home()
                elif kind == 10212:
                    name = (Reader(payload).string() or '').strip()
                    if not 1 <= len(name) <= 20 or any(ord(c) < 32 for c in name):
                        raise ValueError('invalid player name')
                    self.player['name'] = name
                    self.server.store.save(self.player)
                    self.home()
                else:
                    LOG.debug('session=%s UNIMPLEMENTED type=%d', self.session, kind)
        except (ConnectionError, TimeoutError, OSError) as error:
            LOG.info('session=%s DISCONNECT reason=%s', self.session, type(error).__name__)
        except (ValueError, PermissionError) as error:
            LOG.warning('session=%s REJECT reason=%s', self.session, error)
        except Exception:
            LOG.exception('session=%s SERVER_ERROR', self.session)

    def finish(self):
        LOG.info('session=%s CLOSED player=%s', self.session,
                 self.player['id'] if self.player else None)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, store):
        self.store = store
        super().__init__(address, Client)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=9339)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'server/data')
    args = parser.parse_args()
    LOG.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    for handler in [logging.StreamHandler(), RotatingFileHandler(
            ROOT / 'debuglog.txt', maxBytes=5_000_000, backupCount=3, encoding='utf-8')]:
        handler.setFormatter(formatter)
        LOG.addHandler(handler)
    with Server((args.host, args.port), AccountStore(args.data_dir)) as server:
        LOG.info('LISTEN host=%s port=%d storage=SQLite+JSON', args.host, args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            LOG.info('SHUTDOWN')


if __name__ == '__main__':
    main()
