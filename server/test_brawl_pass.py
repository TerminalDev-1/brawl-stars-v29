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
    def special(self, p):
        return next((i for i, o in enumerate(p['offers']['items'])
                     if o.get('section') == shop.SECTION_SPECIAL), None)

    def test_free_colette_comes_fully_kitted(self):
        p = player()
        shop.daily_offers(p)
        index = self.special(p)
        self.assertEqual(p['offers']['items'][index]['cost'], 0)
        self.assertEqual(shop.buy(p, index), [(trophy_road.ITEM_BRAWLER, 39, 1)])
        self.assertIn(39, brawlers.owned(p))
        self.assertEqual(brawlers.power_level(p, 39), brawlers.MAX_LEVEL)
        self.assertEqual(brawlers.points(p, 39), brawlers.MAX_POWER_POINTS)
        self.assertEqual(sorted(p['cards']), [300, 302])
        self.assertIsNone(shop.buy(p, index))
        # Same day: still listed as claimed. After the reset there's nothing left to give.
        shop.daily_offers(p)
        self.assertEqual(self.special(p), index)
        self.assertIn(index, p['offers']['bought'])
        p['offers']['day'] = '2000-01-01'
        shop.daily_offers(p)
        self.assertIsNone(self.special(p))

    def test_owned_colette_offer_maxes_her(self):
        p = player(unlocked=[0, 39], power_points={'39': 100}, power_levels={'39': 2})
        shop.daily_offers(p)
        offer = p['offers']['items'][self.special(p)]
        needed = brawlers.MAX_POWER_POINTS - 100
        self.assertEqual((offer['type'], offer['amount']), (shop.OFFER_POWER_POINTS, needed))
        result = home_commands.Result()
        home_commands.apply(p, home_commands.Command(519, [self.special(p)]), result)
        self.assertTrue(brawlers.maxed(p, 39))
        self.assertEqual(brawlers.points(p, 39), brawlers.MAX_POWER_POINTS)
        # The client still shows her at power 1 until its next home load. An
        # upgrade it sends meanwhile is ignored without a resync or a charge.
        gold = p['gold']
        result = home_commands.Result()
        home_commands.apply(p, home_commands.Command(520, [(16, 39)]), result)
        self.assertFalse(result.resync)
        self.assertEqual(p['gold'], gold)

    def test_home_data_lists_her_cards(self):
        import messages
        p = player(cards=[300, 302])
        p['offers'] = {'day': shop.today(), 'items': [], 'bought': []}
        self.assertIn(bytes([23, 0xac, 0x04]), messages.home_data(p))  # Card 300 (scid 23).

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
            lines = (copy / 'csv_logic' / 'skills.csv').read_text(encoding='utf-8').splitlines()
            weapon = next(l for l in lines if l.startswith('"PercenterWeapon"'))
            ulti = next(l for l in lines if l.startswith('"PercenterUlti"'))
            self.assertIn(',1150,3,1300,,100,', weapon)  # Reload 1150 ms, 1300 flat damage.
            self.assertIn(',1000,20,', ulti)  # Super stays stock.


if __name__ == '__main__':
    unittest.main()


class TrophyAnimationTests(unittest.TestCase):
    def test_battle_win_queues_one_trophy_animation(self):
        import tempfile as tf
        from battles import BotBattle
        from messages import home_data
        from storage import AccountStore
        with tf.TemporaryDirectory() as temp:
            store = AccountStore(temp)
            p, _ = store.login(0, None)
            battle = BotBattle(p['id'])
            store.begin_battle(p['id'], battle.match_id, 13, battle.started_at)
            state = store.complete_battle(p['id'], battle.match_id, 1, 0, 1)['player']
            self.assertEqual(state['trophy_animation'], 500)
            old_best = state['trophies_seen']
            self.assertEqual(state['highest_trophies'], old_best + 500)
            from protocol import Writer
            seen = Writer()
            seen.values(old_best)
            self.assertIn(bytes(seen.bytes()) + bytes([0, 0]), home_data(state))  # The bar fills from here.
            state.pop('trophies_seen')
            with_animation = home_data(state)
            state.pop('trophy_animation')
            self.assertEqual(len(with_animation), len(home_data(state)) + 8)  # One int-value record.
