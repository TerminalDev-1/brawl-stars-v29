# Brawl Stars v29 — private server

A private Python server for Brawl Stars v29, built from scratch, with a
matching Android client hook. The server implements account creation,
token-authenticated reconnects, LoginOk, home data, a starter Shelly
inventory, an event slot, and keepalive replies. Bot-only Gem Grab is
playable from the lobby's Play button. The Android client runs its native
movement, shooting, damage, respawns, gem collection, and bot AI; Python
tracks the active match and handles results and progression. There is one
human and five bots, with no player matchmaking or PvP. Wins award 8
trophies and 20 experience; losses/draws award 10 experience. Leaving
early gives no reward. Most other home commands remain unimplemented.

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

See [client build notes](client_patch/README.md) for local build requirements.
The original APK, native libraries, Android assets, tools, signing keys,
databases, and debug logs are not included in the source repository.

## Tests

```powershell
python -m unittest discover -s server -v
```

Tests cover native integer/boolean wire fixtures, fragmented TCP messages,
parallel connections, authentication, reconnects, keepalive, and JSON recovery.
Bot tests cover match ownership, duplicate results, abandoned matches, TCP
start/result/return, and recovering progression/history from JSON. Device
verification is also necessary for client/native protocol changes.

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

This is a private server, not an official or public release. Android game
assets and other third-party components remain the property of their
respective owners.
