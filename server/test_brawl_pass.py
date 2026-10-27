"""Brawl Pass season 2, the free Colette offer, and Colette's client data edit."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import brawl_pass
import brawlers
import home_commands
import shop
import trophy_road
from protocol import Reader

ROOT = Path(__file__).resolve().parent.parent
# Captured on the tablet: claim free tier 1 and buy the pass.
CLAIM_FREE_TIER_1 = bytes.fromhex('00800800018508bf07bf077f7f0a000201ffffffff')


def player(**extra):
    p = {'id': 2, 'name': 'Player', 'gems': 500, 'gold': 1000, 'trophies': 45,
         'highest_trophies': 45, 'icon': 0, 'name_color': 0, 'brawler': 0, 'theme': 15,
         'unlocked': [0, 8], 'brawl_pass': {'tokens': 1000, 'premium': False, 'free': 0, 'paid': 0}}
    p.update(extra)
    return p


class BrawlPassTests(unittest.TestCase):
    def setUp(self):
        self.box_items = trophy_road.box_items
        trophy_road.box_items = lambda player, box: [(trophy_road.ITEM_GOLD, None, 50)]

    def tearDown(self):
        trophy_road.box_items = self.box_items

    def test_tables_match_season_two(self):
        self.assertEqual(len(brawl_pass.FREE_TRACK), 71)
        self.assertEqual(len(brawl_pass.PREMIUM_TRACK), 50)
        self.assertEqual(brawl_pass.PREMIUM_TRACK[15][1:], (3, 1, 'Percenter'))
        self.assertEqual(brawl_pass.tier(1032), 7)

    def test_captured_claim_delivers_with_season(self):
        p = player()
        commands, _ = home_commands.parse(CLAIM_FREE_TIER_1)
        result = home_commands.Result()
        home_commands.apply(p, commands[0], result)
        self.assertEqual(p['brawl_pass']['free'], brawl_pass.mask_bit(1))
        body = result.replies[0][1]
        self.assertEqual(body[-4:], bytes([0x0a, 0x03, brawl_pass.SEASON, 0x01]))
        # The same tier can't be claimed twice.
        result = home_commands.Result()
        home_commands.apply(p, commands[0], result)
        self.assertTrue(result.resync)

    def test_premium_needs_the_pass_and_enough_tokens(self):
        p = player()
        self.assertIsNone(brawl_pass.claim(p, brawl_pass.PREMIUM, 1))
        self.assertTrue(brawl_pass.buy_pass(p))
        self.assertEqual(p['gems'], 500 - brawl_pass.PASS_PRICE)
        self.assertFalse(brawl_pass.buy_pass(p))
        self.assertIsNotNone(brawl_pass.claim(p, brawl_pass.PREMIUM, 1))
        self.assertIsNone(brawl_pass.claim(p, brawl_pass.PREMIUM, 15))  # Needs 11500 tokens.

    def test_premium_colette_tier_unlocks_her(self):
        p = player()
        p['brawl_pass'].update(tokens=11500, premium=True)
        box, items = brawl_pass.claim(p, brawl_pass.PREMIUM, 15)
        self.assertEqual(items, [(trophy_road.ITEM_BRAWLER, 39, 1)])
        self.assertIn(39, p['unlocked'])

    def test_buy_tier_reaches_next_threshold(self):
        p = player()
        self.assertTrue(brawl_pass.buy_tier(p))
        self.assertEqual(p['brawl_pass']['tokens'], 1300)

    def test_battle_tokens_use_the_doubler(self):
        p = player(token_doubler=10)
        self.assertEqual(brawl_pass.add_tokens(p, 16), (16, 10))
        self.assertEqual((p['brawl_pass']['tokens'], p['token_doubler']), (1026, 0))


class ColetteTests(unittest.TestCase):
    def test_free_colette_offer_until_owned(self):
        p = player()
        shop.daily_offers(p)
        index = next(i for i, o in enumerate(p['offers']['items']) if o['brawler'] == 39)
        self.assertEqual(p['offers']['items'][index]['cost'], 0)
        self.assertEqual(shop.buy(p, index), [(trophy_road.ITEM_BRAWLER, 39, 1)])
        self.assertIn(39, brawlers.owned(p))
        self.assertIsNone(shop.buy(p, index))

    def test_colette_never_drops_from_boxes(self):
        self.assertIn(39, brawlers.BOX_EXCLUDED)

    def test_balance_edit_sets_flat_damage(self):
        sys.path.insert(0, str(ROOT / 'client_patch'))
        import balance
        assets = ROOT / 'client_src' / 'assets'
        if not (assets / 'csv_logic' / 'skills.csv').exists():
            self.skipTest('client assets are local-only')
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp)
            (copy / 'csv_logic').mkdir()
            for name in ('skills.csv', 'characters.csv'):
                shutil.copy(assets / 'csv_logic' / name, copy / 'csv_logic' / name)
            shutil.copy(assets / 'fingerprint.json', copy / 'fingerprint.json')
            balance.apply(copy)
            line = next(l for l in (copy / 'csv_logic' / 'skills.csv').read_text(encoding='utf-8').splitlines()
                        if l.startswith('"PercenterWeapon"'))
            self.assertIn(',1000,,100,', line)  # Damage 1000, no percent damage.


if __name__ == '__main__':
    unittest.main()
