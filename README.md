# Brawl Stars v29 — Python server

A local Python server and matching Android client hook for Brawl Stars v29.
The server implements account creation, token-authenticated reconnects, LoginOk,
home data, a starter Shelly inventory, an event slot, and keepalive replies.
Battle simulation and most home commands are not implemented yet.

The lobby uses v29's pink/purple Gift Shop theme (theme 15), matching the
[Welcome to Starr Park update](https://supercell.com/en/games/brawlstars/blog/release-notes/welcome-to-starr-park/).
Existing accounts on the old default theme are migrated once, preserving
account data. The client hides the native account/server/mod information
overlay; player names, balances, and other normal lobby labels remain visible.

## Run

Requires Python 3.10 or later; the server uses only the standard library.

```powershell
python server/test_server.py
```

The listener defaults to port 9339. Accounts persist in
`server/data/players.sqlite3`. An atomic `server/data/players.json` recovery
snapshot is updated after each login or state change. When the SQLite file is
absent, the server can rebuild it from that JSON snapshot. Preserve both files;
they are private runtime data and are excluded from Git.

`debuglog.txt` records every connection, login, message type/length, error, and
disconnect. It appends across logins and rotates at 5 MB with three older logs.
Account tokens and packet payloads are not written to the log.

## Android client

The release APK is a self-hosting client, with endpoint `127.0.0.1:9339`.
It does not connect to an internet-hosted public backend. With Android platform
tools installed and the tablet connected by USB or wireless debugging:

```powershell
adb install -r --abi armeabi-v7a brawl_v29.apk
adb reverse tcp:9339 tcp:9339
```

Start the Python server, then open Brawl V29. Repeat `adb reverse` after an ADB
reconnect. First launch may show an Android/game notice requiring your choice.
For a direct LAN endpoint, rebuild with `--host YOUR_SERVER_LAN_IP`.

See [client build notes](client_patch/README.md) for local build requirements.
The original APK, native libraries, Android assets, tools, signing keys,
databases, and debug logs are not included in the source repository.

## Tests

```powershell
python -m unittest discover -s server -p test_login.py -v
```

Tests cover native integer/boolean wire fixtures, fragmented TCP messages,
parallel connections, authentication, reconnects, keepalive, and JSON recovery.
Device verification is also necessary for changes to home-data serialization.

## Protocol notes

Messages use a 7-byte big-endian header: type (2), payload length (3), version
(2). Signed variable integers reserve six bits in their first byte and use
sign extension. Adjacent boolean fields share bits in one byte until the next
non-boolean field. The home notification header requires an initial type field
even when the notification count is zero.

Public v29 protocol research was cross-checked against the
[BS-V29 reference implementation](https://github.com/LekmaDev/BS-V29), with final
field alignment checked against the local client's native decoder. No upstream
server is needed at runtime.

This is an independent, unofficial hobby project. Android game assets and
other third-party components remain the property of their respective owners.
