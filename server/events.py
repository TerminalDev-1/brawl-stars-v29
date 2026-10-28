"""Event slots: each mode moves to its next map every five hours.

Map numbers are the client's location IDs. The client skips the blank
continuation rows in locations.csv, so from row 75 on an ID is lower than the
CSV row number (Double Swoosh is CSV row 128 but ID 115).
"""
import time

ROTATION_SECONDS = 5 * 3600

GEM_GRAB_ROTATION = (
    7,    # Hard Rock Mine
    8,    # Crystal Arcade
    10,   # Merch Fort
    11,   # Undermine
    115,  # Double Swoosh
    148,  # Snake Shop
)
SHOWDOWN_ROTATION = (
    14,   # Scorched Stone
    15,   # Rockwall Brawl
    16,   # Feast or Famine
    43,   # Double Trouble
    95,   # Stormy Plains
    13,   # Skull Creek
)
HEIST_ROTATION = (
    18,   # Kaboom Canyon
    19,   # Safe Zone
    23,   # G.G. Mortuary
    53,   # Hot Potato
    71,   # Twist and Shoot
    137,  # Pit Stop
    146,  # Gift Gems
)
BRAWL_BALL_ROTATION = (
    24,   # Backyard Bowl
    25,   # Triple Dribble
    50,   # Sneaky Fields
    51,   # Super Stadium
    132,  # Center Stage
    144,  # Sunny Soccer
    160,  # Field Goal
)

# Event slots in the order the home screen lists them.
SLOTS = (GEM_GRAB_ROTATION, SHOWDOWN_ROTATION, HEIST_ROTATION, BRAWL_BALL_ROTATION)

# Five-hour windows run back to back from the Unix epoch, so the change times
# shift by a few hours each day. Rotations count from the window that started
# 2026-10-28 19:00 UTC, which shows the first map of each list.
FIRST_WINDOW = 1793214000 // ROTATION_SECONDS


def window(now=None):
    return int((time.time() if now is None else now) // ROTATION_SECONDS) - FIRST_WINDOW


def current_maps(now=None):
    """Current map of each slot: (Gem Grab, Showdown, Heist, Brawl Ball)."""
    index = window(now)
    return tuple(rotation[index % len(rotation)] for rotation in SLOTS)


def seconds_left(now=None):
    """Seconds until the next map change."""
    now = time.time() if now is None else now
    return max(1, ROTATION_SECONDS - int(now % ROTATION_SECONDS))
