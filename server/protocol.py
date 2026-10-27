"""v29 Piranha framing, signed variable integers, and packed boolean fields."""
import struct

MAX_PACKET = 2 * 1024 * 1024


class Reader:
    def __init__(self, data):
        self.data, self.offset = memoryview(data), 0

    def take(self, count):
        if count < 0 or self.offset + count > len(self.data):
            raise ValueError("truncated message")
        start = self.offset
        self.offset += count
        return bytes(self.data[start:self.offset])

    def integer(self):
        return struct.unpack('>i', self.take(4))[0]

    def string(self):
        size = self.integer()
        if size == -1:
            return None
        if not 0 <= size <= 65536:
            raise ValueError("invalid string length")
        return self.take(size).decode('utf-8')

    def vint(self):
        value, shift, negative = 0, 0, False
        for index in range(5):
            byte = self.take(1)[0]
            if index == 0:
                negative = bool(byte & 64)
                value = byte & 63
                shift = 6
            else:
                value |= (byte & 127) << shift
                shift += 7
            if not byte & 128:
                return value - (1 << shift) if negative else value
        raise ValueError("invalid variable integer")


class Writer:
    def __init__(self):
        self.data = bytearray()
        self.bit_index = None

    def integer(self, value):
        self.bit_index = None
        self.data.extend(struct.pack('>i', value))

    def boolean(self, value):
        if self.bit_index is None:
            self.data.append(0)
            self.bit_index = 0
        if value:
            self.data[-1] |= 1 << self.bit_index
        self.bit_index += 1
        if self.bit_index == 8:
            self.bit_index = None

    def string(self, value=None):
        if value is None:
            self.integer(-1)
        else:
            raw = value.encode('utf-8')
            self.integer(len(raw))
            self.data.extend(raw)

    def vint(self, value):
        self.bit_index = None
        negative = value < 0
        byte = (value & 63) | (64 if negative else 0)
        value >>= 6
        done = value == (-1 if negative else 0)
        self.data.append(byte | (0 if done else 128))
        if done:
            return
        while True:
            byte = value & 127
            value >>= 7
            done = value == (-1 if negative else 0)
            self.data.append(byte | (0 if done else 128))
            if done:
                break

    def values(self, *values):
        for value in values:
            self.vint(value)

    def reference(self, table, row):
        self.values(table, row)

    def long(self, value):
        self.integer(0)
        self.integer(value)

    def bytes(self):
        return bytes(self.data)


def packet(message_type, payload=b'', version=0):
    if len(payload) > MAX_PACKET:
        raise ValueError("packet too large")
    return (message_type.to_bytes(2, 'big') + len(payload).to_bytes(3, 'big') +
            version.to_bytes(2, 'big') + payload)


def recv_exact(sock, size):
    result = bytearray()
    while len(result) < size:
        chunk = sock.recv(size - len(result))
        if not chunk:
            raise ConnectionError("client disconnected")
        result.extend(chunk)
    return bytes(result)
