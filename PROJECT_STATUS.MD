# Project status

Last updated: 2026-10-27.

## Current release and repository

- Public repository: https://github.com/TerminalDev-1/brawl-stars-v29
- Active development branch: main, tracking origin/main.
- Remote branch inventory verified on 2026-10-27: main is the only remote
  branch. There are no outstanding remote branches to merge or delete.
- Latest published APK: v0.3.2, faster Colette and 500-trophy wins.
  https://github.com/TerminalDev-1/brawl-stars-v29/releases/tag/v0.3.2
- Release commit: 5a21f346909fea6c3a1e97705b613f99e2588250.
- APK SHA256:
  2a5e201e0c8e0f644e97f841ea3fa9759739cc3dd36c5cc638cd8dc1138ef2a9.
- Verified 2026-10-27: public, not a draft, GitHub's asset digest matches the
  local build, and the build is byte-identical to the APK on the tablet.
- Earlier releases: v0.3.1 (APK SHA256
  23b7253c511aefa231914bb43e176026d363078c95427f05c0bf4a14ccc2c235), v0.3.0 (APK SHA256
  3cb525e3cf1ed7aff8f916216320bdba97d5c82670896a33d0ca025e4e411904).
- Previous release: v0.2.0 (bot-only Gem Grab), APK SHA256
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
- Trophy rewards (2026-10-27): a Gem Grab win gives +500 (losses and draws 0).
  Showdown placements 1-10 give +500, +400, +300, +200, +100, -8, -12, -16, -23,
  -25. A brawler can't drop below 0 trophies, highest trophies never decrease,
  and the trophy fly-in plays only for gains. Verified on the tablet: an 8th
  place showed -16 on the results screen and was saved.
- Trophy Road rewards can be collected (2026-10-27). The client's claim command
  (517 inside message 14102) is answered with a delivery (24111 / command 203)
  using the v29 Trophy Road table (milestones.csv track 6): Brawl/Big/Mega Box
  contents (coins, power points, sometimes gems), Trophy Road brawlers (Nita,
  Colt, Bull, ...), coins, power points, token doublers, and the event unlocks.
  Progress, unlocked brawlers, power points, and per-brawler trophies are saved
  and sent back in home data after a relog. Claims beyond the player's highest
  trophies are refused and the home screen is resynchronized.
- Brawlers menu and Shop work (2026-10-27). Home commands batched in 14102 are
  parsed one by one (home_commands.py) and repeated on the server so they
  persist: selecting a brawler and its skin (525/506), upgrading a brawler (520,
  v29 coin and power point costs, lifetime power point totals as the client
  counts them), buying Big/Mega Boxes for gems (500, contents delivered with
  24111/203, boxes can drop new non-common brawlers), the Token Doubler (509),
  the 1000-coin pack (521), and daily deals (519). Daily deals offer power
  points for owned brawlers for coins, refresh at midnight, and show Purchased
  once bought. Purchases the player can't afford are refused and the home
  screen is resent.
- Colette, Brawl Pass and Showdown fixes (2026-10-27):
  - Client build applies game-data edits from client_patch/balance.py: Colette's
    main attack does a flat 1300 damage (the percent-of-health damage is
    removed), she reloads in 1150 ms per shot (stock 1800 ms), she moves 15%
    faster (speed 828, stock 720; stats show VERY FAST), and her hidden
    flag is cleared so she appears in the collection. Her Super stays stock
    (20% of max health): her dash type always deals percent damage, and its
    Damage field only applies to special targets. A flat 2000 was tried on the
    device and still dealt percent damage, so it was reverted.
  - The shop always has a FREE COLETTE! offer. Before she is owned it unlocks
    her; afterwards it gives 100 Colette power points once per day (the client
    hides it after it is claimed until the daily reset). She never drops from
    boxes.
- Trophy fly-in animation (2026-10-27): after a battle that gains trophies, home
  data carries the trophies won (int-value record 4) once, and the home screen
  plays the trophy count-up animation. Verified on the tablet: the counter went
  51 -> 61 with +10 flying in after a Showdown win; the animation plays once.
  - Brawl Pass season 2 (Starr Park / Colette) from milestones.csv: battles give
    tokens (Token Doubler doubles them), free and premium tiers can be claimed
    once each (deliveries carry season 2, which the client requires), the pass
    costs 169 gems (534) and single tiers 30 gems (536). Colette is the premium
    tier-15 reward; Poco Starr and Trixie Colette skins are recorded as owned.
  - Showdown results below 2nd place were rejected (the client reports the
    placement in the result field too). They are now accepted, and the results
    screen shows the brawler's own trophies and the Token Doubler balance.
- Solo Showdown (Skull Creek) is the second event slot next to Gem Grab. The
  client unlocks it at the 30-trophy Trophy Road step, as in the original game.
  Matches run with nine bots; the result screen shows the placement, and rewards
  are 10/8/7/6/4/2/2/1/0/0 trophies by rank with no trophy loss.
- SQLite stores accounts, match history, and progression. Atomic JSON snapshots
  support recovery when the SQLite database is absent.
- debuglog.txt records connection, login, protocol, and match diagnostics,
  appending across logins and rotating at 5 MB with three older logs. Tokens
  and raw account payloads are not logged.

## Verification evidence

Verified on 2026-10-27 for the second Colette update and the trophy animation
(published as v0.3.1):

- All 40 automated server tests passed.
- On the tablet: Colette's stats show Damage 1300 and Reload Speed VERY FAST; in
  training one shot took a 4000-health dummy to 2700. The results screen shows
  the brawler's own trophies and the real Token Doubler balance (1456 left after
  doubling 22 tokens to 44).

Verified on 2026-10-27 for Colette, Brawl Pass and the Showdown fix (APK rebuilt,
installed on the tablet and published as v0.3.0):

- All 38 automated server tests passed, including 10 new tests (captured Brawl
  Pass claim, premium rules, tier purchase, token doubling, free Colette offer,
  and the Colette data edit on a copy of the assets).
- On the tablet (scratch copy of the account): claimed FREE COLETTE!, Colette
  appeared as NEW with Brawlers 3/39, her stats show Damage 1000, and in the
  training ground one shot took a 4000-health dummy to exactly 3000. After the
  reload change her stats show Reload Speed FAST (was NORMAL) and the ammo bar
  refills in training; exact reload timing was not measured with a stopwatch.
- Played Solo Showdown with Colette: 4th place was accepted with +6 trophies and
  +16 tokens. Claimed free Brawl Pass tiers (Big Box), bought the pass for 169
  gems and claimed a premium Mega Box; claimed tiers show checkmarks after relog.
- The real account logged in afterwards with the Brawl Pass at tier 1.

Verified on 2026-10-27 for the Brawlers menu and Shop (server-only change):

- All 28 automated server tests passed, including 9 new tests that replay
  command batches captured from the tablet.
- On the tablet (scratch copy of the account): selected Nita and later Shelly,
  bought a Big Box (coins and power points delivered), a Token Doubler, the
  1000-coin pack and a Nita daily deal, and upgraded Nita and Shelly to power 2.
  After restarting the app, the selected brawler, power levels, power point
  bars, coins, gems, Token Doubler and the Purchased deal were all unchanged.
- The real account logged in with the new shop and its own daily deal, with no
  crash. Gem packs are real-money Google Play purchases and are not supported.

Verified on 2026-10-27 for Trophy Road and Showdown (server-only change; the
v0.2.0 APK is unchanged):

- All 19 automated server tests passed, including 8 new tests for claim order,
  unlock steps, delivery encoding against the captured native claim, home data
  with extra brawlers, Showdown result parsing, and Showdown rewards.
- On the tablet (against a scratch copy of the account database): the Brawl Box
  at 5 trophies opened with coins and Shelly power points, Nita unlocked at 10,
  the box at 20 opened, and the Showdown unlock at 30 opened Choose Event with
  Showdown listed. Coins and the claimed steps persisted across a relog.
- A Solo Showdown match ran with bots, ended on "You are #1! +10", and Proceed
  returned to the lobby with the new trophy total.
- The real account was not used for these claims; its three earned rewards are
  still waiting to be collected.

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

`start_server.bat` does all of this in one step (2026-10-28). It first stops
any leftover Python server listening on port 9339, then runs the ADB reverse
and warns if no tablet is connected (plug in USB or turn on Wireless
debugging), then starts the server. This fixes the tablet hanging on
"connecting to server": a stale server left bound to 127.0.0.1:9339 took the
forwarded connection instead of the new one, because Windows prefers the
specific address over 0.0.0.0. Verified on the tablet: the launcher stopped
two old servers, the new one logged LOGIN_OK for player 2, and the home screen
loaded with saved progress.

## Remaining work and constraints

- Battles use native local bot simulation; Python does not simulate real-time
  combat. PvP and player matchmaking are not implemented.
- Playable events are Gem Grab and Solo Showdown. Duo Showdown results are
  accepted by the server but have not been tested on the device.
- Brawl Pass quests, pins and selecting the pass skins are not implemented;
  the 249-gem Brawl Pass bundle and buying tiers were not tested on the device.
  Colette's Super still uses its percent damage (not changeable through game
  data). Profile, club, friends, chat,
  gadgets and star powers are still unimplemented; unknown commands are logged as
  UNIMPLEMENTED with their bytes. Trophies are credited to the brawler reported
  in the match result. Gem packs (real money) cannot be bought.
- A Gem Grab or Showdown match played with a brawler other than Shelly has not
  yet been checked on the device.
- The experimental stock native-library profile still has its original
  startup failure. Use the matched reference libraries and companion
  initialization described in client_patch/README.md.
- Live databases, JSON snapshots, logs, credentials, signing keys, private
  notes, device details, and third-party game assets stay out of public source.
- Client bot difficulty is decided in the client's native code (nothing in the
  game data or the reference server controls it); capping it is not done yet.
- Future verified changes must update this file before commit and push.
  PROJECT_RULES.md requires a published release whenever the APK changes.
  Work stays on main, and a request to commit includes pushing to origin/main.
