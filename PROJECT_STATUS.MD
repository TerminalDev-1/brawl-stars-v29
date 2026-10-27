# Project status

Last updated: 2026-10-27.

## Current release and repository

- Public repository: https://github.com/TerminalDev-1/brawl-stars-v29
- Active development branch: main, tracking origin/main.
- Remote branch inventory verified on 2026-10-27: main is the only remote
  branch. There are no outstanding remote branches to merge or delete.
- Latest published APK: v0.2.0, playable bot-only Gem Grab.
  https://github.com/TerminalDev-1/brawl-stars-v29/releases/tag/v0.2.0
- Gameplay implementation commit: f46314cf731a2d6c2c62f53172f8ef057ea5d5a0.
- APK SHA256:
  ad9f652f1fdffc92fcbe3ca8142250799c020cfbfe3136d57b6b11019aad797c.
- Earlier local history is preserved by the local-only tag
  archive/local-main-before-unification-20261027. Preserve that history locally;
  it contains private notes that are excluded from the public source.

## Verified functionality

- Account creation, token-authenticated login, reconnect, home data, and
  keepalive work with the matched v29 Android client.
- The lobby uses the original pink/purple Gift Shop theme. The native debug
  overlay is hidden while normal player and balance labels remain visible.
- Play starts Gem Grab on Hard Rock Mine with one human and five bots.
  Native client simulation handles movement, shooting, bot AI, damage,
  respawns, gems, countdown, and match completion.
- Python tracks active matches, validates reported participants and teams,
  sends the results screen, and saves progression. Wins give 8 trophies and
  20 experience; losses and draws give 10 experience without a trophy penalty.
- Leaving early returns home without a reward. Duplicate completed results
  cannot award progression twice. Another battle can be started after returning.
- SQLite stores accounts, match history, and progression. Atomic JSON snapshots
  support recovery when the SQLite database is absent.
- debuglog.txt records connection, login, protocol, and match diagnostics,
  appending across logins and rotating at 5 MB with three older logs. Tokens
  and raw account payloads are not logged.

## Verification evidence

Verified on 2026-10-27 for v0.2.0:

- All 11 automated server tests passed: native wire fixtures, fragmented TCP,
  authentication, parallel connections, reconnects, keepalive, theme migration,
  result validation, match ownership, abandonment, duplicate rewards,
  loss/draw rewards, native results flags, and SQLite/JSON recovery.
- The normal release APK passed repeated login/home launch checks on the
  connected Android tablet.
- Device checks covered movement, shooting, bot combat, damage and respawns,
  a full round, the correct results roster, trophy/experience rewards,
  early exit, lobby return, starting another match, and persistence after
  restarting the client.
- Published APK digest matched the locally installed build. The repository
  was public and the v0.2.0 release was published with APK and checksum assets.

Run the automated suite with:

```powershell
python -m unittest discover -s server -v
```

## Running the game

```powershell
python server/test_server.py
adb reverse tcp:9339 tcp:9339
```

The release APK connects to 127.0.0.1:9339 on the tablet, forwarded to the PC's
Python server by ADB. Repeat the reverse command after reconnecting ADB. A LAN
endpoint requires a rebuild with the desired host; this release does not use
an internet-hosted public backend.

## Remaining work and constraints

- Battles use native local bot simulation; Python does not simulate real-time
  combat. PvP and player matchmaking are not implemented.
- The supported playable flow is the starter Shelly inventory and the Gem Grab
  event. Most other home commands, shop/progression reward claims, and broader
  game systems remain unimplemented. A Trophy Road reward prompt may appear as
  trophies increase; reward collection is not part of the verified flow.
- The experimental stock native-library profile still has its original
  startup failure. Use the matched reference libraries and companion
  initialization described in client_patch/README.md.
- Live databases, JSON snapshots, logs, credentials, signing keys, private
  notes, device details, and third-party game assets stay out of public source.
- Future verified changes must update this file before commit and push.
  Work stays on main, and a request to commit includes pushing to origin/main.
