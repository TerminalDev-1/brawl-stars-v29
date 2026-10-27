// Brawl Stars v29 (29.270, armeabi-v7a) client hook for Frida Gadget 17.
// The builder supplies the profile matching the selected, hash-checked libraries.
//
// What it does:
//  1. Redirects the game's connection on port 9339 to our own server.
//  2. Skips the game's encryption completely: messages are taken from the
//     game's send queue and written raw to the socket, and raw packets from
//     the socket are decoded and pushed into the game's receive queue.
//
// Packet format on the wire (both directions):
//   [type: u16 BE][payload length: u24 BE][version: u16 BE][payload]

'use strict';

const CONFIG = {
  host: '127.0.0.1',
  port: 9339,
  ...(globalThis.V29_SERVER_CONFIG || {}),
};

// Addresses differ between the stock and reference 29.270 native builds.
const PROFILES = {
  stock: {
    serverConnection: 0xc65f34,    // global: ServerConnection*
    createMessageByType: 0x4bd798, // createMessageByType(factory, type)
  },
  reference: {
    serverConnection: 0xc86d10,
    createMessageByType: 0x4a7ee4,
    lobbyDebugGetter: 0x6db4, // Function in the matched native companion.
    lobbyDebugReturn: 0x5c37f4,
  },
};
const OFFSETS = PROFILES[globalThis.V29_LIBRARY_PROFILE || 'reference'];

// Struct layouts (32-bit).
const SC_MESSAGING = 0x4;        // ServerConnection -> Messaging*
const MSG_FACTORY = 0x34;        // Messaging -> MessageFactory*
const MSG_RECV_QUEUE = 0x3c;     // Messaging -> receive queue (inline)
const MSG_SEND_QUEUE = 0x54;     // Messaging -> send queue (inline)
const MSG_STATE = 0xd0;          // Messaging -> connection state
const MSG_LOGIN_MESSAGE = 0xd4;  // Messaging -> pending LoginMessage*

const STATE_LOGGED_IN = 5;
const CLIENT_HELLO = 10100;
const LOGIN_OK = 20104;

const MSG_DONTWAIT = 0x40;
const EAGAIN = 11;

// ---------- libc ----------
const libc = Process.getModuleByName('libc.so');
const cfn = (name, ret, args) => new NativeFunction(libc.getExportByName(name), ret, args);
const malloc = cfn('malloc', 'pointer', ['uint']);
const free = cfn('free', 'void', ['pointer']);
const memmove = cfn('memmove', 'pointer', ['pointer', 'pointer', 'uint']);
const libcSend = cfn('send', 'int', ['int', 'pointer', 'uint', 'int']);
const libcRecv = new SystemFunction(libc.getExportByName('recv'), 'int', ['int', 'pointer', 'uint', 'int']);
const mutexLock = cfn('pthread_mutex_lock', 'int', ['pointer']);
const mutexUnlock = cfn('pthread_mutex_unlock', 'int', ['pointer']);
const inetAddr = cfn('inet_addr', 'uint32', ['pointer']);

const androidLog = new NativeFunction(
  Process.getModuleByName('liblog.so').getExportByName('__android_log_write'),
  'int', ['int', 'pointer', 'pointer']);
const logTag = Memory.allocUtf8String('v29');
const log = (...a) => androidLog(4, logTag, Memory.allocUtf8String(a.map(String).join(' ')));

// ---------- game objects ----------
const vcall = (obj, slot, ret, args) =>
  new NativeFunction(obj.readPointer().add(slot).readPointer(), ret, ['pointer', ...args]);

const Message = {
  type: (m) => vcall(m, 0x14, 'int', [])(m),
  encode: (m) => vcall(m, 0x08, 'void', [])(m),
  decode: (m) => vcall(m, 0x0c, 'void', [])(m),
  version: (m) => m.add(0x4).readS32(),
  setVersion: (m, v) => m.add(0x4).writeS32(v),
  stream: (m) => m.add(0x8),
};

const ByteStream = {
  offset: (s) => s.add(0x10).readS32(),
  setLength: (s, n) => s.add(0x14).writeS32(n),
  data: (s) => s.add(0x1c).readPointer(),
  setData: (s, p) => s.add(0x1c).writePointer(p),
};

// Ring buffer of Message*, guarded by a mutex stored 4 bytes before it.
const Queue = {
  items: (q) => q.readPointer(),
  capacity: (q) => q.add(0x4).readS32(),
  count: (q) => q.add(0x8).readS32(),
  setCount: (q, n) => q.add(0x8).writeS32(n),
  head: (q) => q.add(0xc).readS32(),
  setHead: (q, n) => q.add(0xc).writeS32(n),
  tail: (q) => q.add(0x10).readS32(),
  setTail: (q, n) => q.add(0x10).writeS32(n),
  lock: (q) => mutexLock(q.sub(4)),
  unlock: (q) => mutexUnlock(q.sub(4)),

  push(q, msg) {
    Queue.lock(q);
    const t = Queue.tail(q);
    Queue.items(q).add(t * 4).writePointer(msg);
    Queue.setTail(q, (t + 1) % Queue.capacity(q));
    Queue.setCount(q, Queue.count(q) + 1);
    Queue.unlock(q);
  },

  pop(q) {
    let msg = null;
    Queue.lock(q);
    if (Queue.count(q) > 0) {
      const h = Queue.head(q);
      msg = Queue.items(q).add(h * 4).readPointer();
      Queue.setHead(q, (h + 1) % Queue.capacity(q));
      Queue.setCount(q, Queue.count(q) - 1);
    }
    Queue.unlock(q);
    return msg;
  },
};

// ---------- connection state ----------
const conn = {
  fd: -1,
  messaging: null,
  factory: null,
  createMessage: null,
  rx: new Uint8Array(0),   // bytes received but not yet a full packet
  gameBase: null,
  gameEnd: null,
  lobbyOverlayHook: null,
};

function setupMessaging() {
  const libg = Process.getModuleByName('libg.so');
  hideLobbyDebugText(libg);
  conn.gameBase = libg.base;
  conn.gameEnd = libg.base.add(libg.size);
  const serverConnection = libg.base.add(OFFSETS.serverConnection).readPointer();
  conn.messaging = serverConnection.add(SC_MESSAGING).readPointer();
  conn.factory = conn.messaging.add(MSG_FACTORY).readPointer();
  conn.createMessage = new NativeFunction(libg.base.add(OFFSETS.createMessageByType), 'pointer', ['pointer', 'int']);
  log('messaging at', conn.messaging, 'factory at', conn.factory);
}

function hideLobbyDebugText(libg) {
  if (OFFSETS.lobbyDebugGetter === undefined || conn.lobbyOverlayHook !== null) return;
  const helper = Process.findModuleByName('lib39285EFA.so');
  if (helper === null) return;
  const caller = libg.base.add(OFFSETS.lobbyDebugReturn);
  let logged = false;
  conn.lobbyOverlayHook = Interceptor.attach(helper.base.add(OFFSETS.lobbyDebugGetter), {
    onEnter() {
      if (!this.returnAddress.equals(caller)) return;
      // At this call site r4 is the home screen and +0x1e0 is its debug
      // TextField. DisplayObject's alpha byte is +8. The game refreshes
      // this one label every frame; keep its alpha zero across those updates.
      const label = this.context.r4.add(0x1e0).readPointer();
      if (label.isNull()) return;
      label.add(8).writeU8(0);
      if (!logged) { logged = true; log('lobby debug overlay hidden'); }
    },
  });
}

// ---------- sending ----------
function sendRaw(msg) {
  Message.encode(msg);
  const type = Message.type(msg);
  const stream = Message.stream(msg);
  const len = ByteStream.offset(stream);

  const buf = malloc(len + 7);
  buf.writeU8((type >> 8) & 0xff);
  buf.add(1).writeU8(type & 0xff);
  buf.add(2).writeU8((len >> 16) & 0xff);
  buf.add(3).writeU8((len >> 8) & 0xff);
  buf.add(4).writeU8(len & 0xff);
  const ver = Message.version(msg);
  buf.add(5).writeU8((ver >> 8) & 0xff);
  buf.add(6).writeU8(ver & 0xff);
  if (len > 0) memmove(buf.add(7), ByteStream.data(stream), len);
  libcSend(conn.fd, buf, len + 7, 0);
  free(buf);
  log('sent', type, 'len', len);
}

function flushSendQueue() {
  const q = conn.messaging.add(MSG_SEND_QUEUE);
  let msg;
  while ((msg = Queue.pop(q)) !== null) {
    if (Message.type(msg) === CLIENT_HELLO) {
      // Skip the encryption handshake: send the pending LoginMessage instead.
      const slot = conn.messaging.add(MSG_LOGIN_MESSAGE);
      const login = slot.readPointer();
      if (login.isNull()) continue;
      slot.writePointer(ptr(0));
      msg = login;
    }
    sendRaw(msg);
  }
}

// ---------- receiving ----------
function readSocket() {
  const chunk = 4096;
  const tmp = malloc(chunk);
  for (;;) {
    const r = libcRecv(conn.fd, tmp, chunk, MSG_DONTWAIT);
    if (r.value <= 0) break; // no data (EAGAIN), closed, or error
    const add = new Uint8Array(tmp.readByteArray(r.value));
    const merged = new Uint8Array(conn.rx.length + add.length);
    merged.set(conn.rx);
    merged.set(add, conn.rx.length);
    conn.rx = merged;
  }
  free(tmp);
}

function deliver(type, version, payload) {
  const msg = conn.createMessage(conn.factory, type);
  if (msg.isNull()) {
    log('unknown message type from server:', type);
    return;
  }
  Message.setVersion(msg, version);
  const stream = Message.stream(msg);
  ByteStream.setLength(stream, payload.length);
  if (payload.length > 0) {
    const data = malloc(payload.length);
    data.writeByteArray(payload);
    ByteStream.setData(stream, data);
  }
  Message.decode(msg);
  if (type === LOGIN_OK) conn.messaging.add(MSG_STATE).writeS32(STATE_LOGGED_IN);
  Queue.push(conn.messaging.add(MSG_RECV_QUEUE), msg);
  log('received', type, 'len', payload.length);
}

function pumpReceive() {
  readSocket();
  const b = conn.rx;
  let pos = 0;
  while (b.length - pos >= 7) {
    const type = (b[pos] << 8) | b[pos + 1];
    const len = (b[pos + 2] << 16) | (b[pos + 3] << 8) | b[pos + 4];
    const version = (b[pos + 5] << 8) | b[pos + 6];
    if (b.length - pos - 7 < len) break; // wait for the rest
    deliver(type, version, Array.from(b.subarray(pos + 7, pos + 7 + len)));
    pos += 7 + len;
  }
  if (pos > 0) conn.rx = b.slice(pos);
}

// ---------- hooks ----------
function isGameCaller(address) {
  return conn.gameBase !== null && address.compare(conn.gameBase) >= 0 &&
    address.compare(conn.gameEnd) < 0;
}

Interceptor.attach(libc.getExportByName('connect'), {
  onEnter(args) {
    const addr = args[1];
    if (addr.readU16() !== 2) return; // AF_INET only
    const p = addr.add(2);
    const port = (p.readU8() << 8) | p.add(1).readU8();
    if (port !== 9339) return;

    addr.add(4).writeU32(inetAddr(Memory.allocUtf8String(CONFIG.host)));
    p.writeU8((CONFIG.port >> 8) & 0xff);
    p.add(1).writeU8(CONFIG.port & 0xff);
    conn.fd = args[0].toInt32();
    conn.rx = new Uint8Array(0);
    log('redirecting game connection to', CONFIG.host + ':' + CONFIG.port, 'fd', conn.fd);
    setupMessaging();
  },
});

// The messaging thread signals a condition variable when it queues a message.
Interceptor.attach(libc.getExportByName('pthread_cond_signal'), {
  onEnter() {
    if (isGameCaller(this.returnAddress) && conn.messaging !== null && conn.fd >= 0) flushSendQueue();
  },
});

// The network thread calls select() in its loop; use it to poll the socket.
Interceptor.attach(libc.getExportByName('select'), {
  onEnter(args) {
    this.readSet = null;
    if (!isGameCaller(this.returnAddress) || conn.messaging === null || conn.fd < 0 || args[1].isNull()) return;
    const word = args[1].add((conn.fd >>> 5) * 4);
    const mask = (1 << (conn.fd & 31)) >>> 0;
    if ((word.readU32() & mask) === 0) return;
    this.readSet = word;
    this.mask = mask;
  },
  onLeave(result) {
    if (this.readSet === null || result.toInt32() <= 0 || (this.readSet.readU32() & this.mask) === 0) return;
    try {
      // Consume plaintext after select becomes readable, before the native
      // encrypted receive path can read the same socket.
      pumpReceive();
      this.readSet.writeU32((this.readSet.readU32() & ~this.mask) >>> 0);
      result.replace(Math.max(0, result.toInt32() - 1));
    } catch (error) {
      log('receive error', String(error));
    }
  },
});

log('script loaded, server =', CONFIG.host + ':' + CONFIG.port);
