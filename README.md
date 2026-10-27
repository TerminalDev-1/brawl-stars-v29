# Brawl Stars v29 — private server

This is a private server for Brawl Stars v29, written from scratch in
Python, with an Android client patched to talk to it instead of
Supercell's servers. You can create an account, log in, sit in the lobby
(Shelly as your starting Brawler, Coins, Gems, an event slot), and
actually play bot matches: Gem Grab (3v3, you and two bot teammates
against three bots) and Solo Showdown (you against nine bots), with real
movement, shooting, damage, respawns and gems running client-side. Python
tracks the match and hands out the results — 250 Trophies and 20 XP for a
Gem Grab win, 10 XP for a loss or draw; in Showdown, 1st to 5th place give
+250/+200/+150/+100/+50 and 6th to 10th lose 8/12/16/23/25. Nothing if you
quit early. Trophy Road rewards can be collected:
boxes, new Brawlers like Nita, coins and power points. Showdown unlocks at
30 trophies on the Trophy Road, like the original game. In the Brawlers
menu you can pick any Brawler you own and upgrade it with coins and power
points. The Shop sells Big and Mega Boxes, the Token Doubler and a coin
pack for gems, plus daily deals (power points for coins) that refresh at
midnight, plus a free Colette offer that never goes away (after you own
her it gives free Colette power points once a day). Colette's attack is
buffed to a flat 1300 damage per shot instead of percent-of-health, and
she reloads in 1.15 seconds instead of 1.8. After a battle the home screen
plays the trophy fly-in animation. The Brawl Pass works: battles
earn tokens, and you can claim free rewards, buy the pass for 169 gems and
claim the premium track (Poco Starr, Colette, Trixie Colette). Gem packs
cost real money in the original game and don't work here. Clubs, friends,
chat and Brawl Pass quests aren't built yet.

The lobby uses v29's pink/purple Gift Shop theme (theme 15), matching the
[Welcome to Starr Park update](https://supercell.com/en/games/brawlstars/blog/release-notes/welcome-to-starr-park/).
Old accounts get migrated off the default theme once, without losing
anything. The client's native account/server/mod overlay is hidden, but
normal lobby labels — name, balances, etc. — stay visible.

## Running the server

Needs Python 3.10+, nothing else — standard library only.

```powershell
python server/test_server.py
```

Listens on port 9339 by default. Accounts live in
`server/data/players.sqlite3`, with a JSON snapshot
(`server/data/players.json`) kept in sync after every login or state
change, so the server can rebuild the database from it if needed. Both
files are private runtime data and stay out of Git — don't delete them.

`debuglog.txt` logs every connection, login, message, error and
disconnect (no tokens, no raw payloads), rotating at 5 MB with three
backups kept.

## Connecting the Android client

The release APK is self-contained — it points at `127.0.0.1:9339` and
never talks to the real Brawl Stars servers. With the tablet on USB or
wireless debugging and platform-tools installed:

```powershell
adb install -r --abi armeabi-v7a brawl_v29.apk
adb reverse tcp:9339 tcp:9339
```

Start the Python server first, then open Brawl V29. If ADB reconnects,
redo the `adb reverse` line. The first launch may throw up an
Android/game notice you'll need to dismiss. Want it reachable over the
LAN instead of just the loopback forward? Rebuild with
`--host YOUR_SERVER_LAN_IP`.

Local build steps are in [client_patch/README.md](client_patch/README.md).
The original APK, native libraries, Android assets, signing keys,
databases and debug logs aren't in this repo.

## Tests

```powershell
python -m unittest discover -s server -v
```

Covers the wire format (ints, booleans, fragmented TCP, parallel
connections), auth and reconnects, keepalive, and JSON recovery, plus
battle-specific coverage: match ownership, duplicate results, abandoned
matches, and the full start/result/return cycle. Anything touching the
client's native protocol still needs a real device check on top of this.

## Protocol notes

7-byte big-endian header on every message: type (2 bytes), payload
length (3 bytes), version (2 bytes). Signed varints reserve six bits in
their first byte and sign-extend. Adjacent booleans pack into shared bits
until the next non-boolean field breaks the run. The home notification
header needs its type field even at zero notifications — easy to miss.

Protocol details were cross-checked against the
[BS-V29 reference implementation](https://github.com/LekmaDev/BS-V29),
with final field layout confirmed against the client's own native
decoder. Nothing here talks to an upstream server at runtime.

This is a private server, not an official release. Android game assets
and everything else third-party still belong to their original owners.
