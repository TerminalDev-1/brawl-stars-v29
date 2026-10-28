"""Event slots and their five-hour map rotation."""
import unittest

import battles
import events
import messages
import shop

START = 1793214000  # 2026-10-28 19:00 UTC, the first rotation window.
HOURS = 3600


class RotationTests(unittest.TestCase):
    def test_four_modes_and_showdown_off_skull_creek(self):
        # Hard Rock Mine, Scorched Stone, Kaboom Canyon, Backyard Bowl.
        self.assertEqual(events.current_maps(START), (7, 14, 18, 24))
        self.assertEqual(events.current_maps(START + 5 * HOURS - 1), (7, 14, 18, 24))

    def test_maps_change_every_five_hours(self):
        self.assertEqual(events.current_maps(START + 5 * HOURS), (8, 15, 19, 25))
        self.assertEqual(events.current_maps(START + 10 * HOURS), (10, 16, 23, 50))

    def test_each_rotation_wraps_around(self):
        for slot, rotation in enumerate(events.SLOTS):
            seen = [events.current_maps(START + i * 5 * HOURS)[slot] for i in range(2 * len(rotation))]
            self.assertEqual(seen, list(rotation) * 2)

    def test_timer_counts_down_to_the_change(self):
        self.assertEqual(events.seconds_left(START), 5 * HOURS)
        self.assertEqual(events.seconds_left(START + 5 * HOURS - 30), 30)

    def test_every_rotation_map_is_accepted_in_results(self):
        team = set(events.GEM_GRAB_ROTATION) | set(events.HEIST_ROTATION) | set(events.BRAWL_BALL_ROTATION)
        self.assertEqual(battles.TEAM_MAPS, team)
        self.assertTrue(set(events.SHOWDOWN_ROTATION) <= battles.SHOWDOWN_MAPS)
        self.assertFalse(battles.TEAM_MAPS & battles.SHOWDOWN_MAPS)

    def test_home_data_lists_four_event_slots(self):
        p = {'id': 2, 'name': 'Player', 'gems': 0, 'gold': 0, 'trophies': 0, 'icon': 0,
             'name_color': 0, 'brawler': 0, 'theme': 15, 'unlocked': [0]}
        p['offers'] = {'day': shop.today(), 'items': [], 'bought': []}
        data = messages.home_data(p)
        self.assertIn(bytes([5, 0, 1, 2, 3, 4, 4]), data)  # Slot IDs 0-4, then four events.


if __name__ == '__main__':
    unittest.main()
