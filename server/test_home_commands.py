"""Brawler menu and shop commands, using batches captured from the v29 client."""
import unittest

import brawlers
import home_commands
import shop
import trophy_road
from messages import home_data
from protocol import Reader

# Captured on the tablet.
SELECT_NITA = bytes.fromhex('00b0090002ba07af09af097f7f1d0e8d08af09af097f7f1008ffffffff')
SHOP_OPENED = bytes.fromhex('00851600018308841684167f7f06017f7fffffffff')
BUY_BIG_BOX = bytes.fromhex('00831c0001b407821c821c7f7f01ffffffff')
BUY_TOKEN_DOUBLER = bytes.fromhex('009a140001bd07991499147f7fffffffff')
NITA_SEEN = bytes.fromhex('00b80600018a08b706b7067f7f100800000002ffffffff')


def player(**extra):
    p = {'id': 2, 'name': 'Player', 'gems': 100, 'gold': 1000, 'trophies': 45,
         'highest_trophies': 45, 'icon': 0, 'name_color': 0, 'brawler': 0, 'theme': 15,
         'unlocked': [0, 8]}
    p.update(extra)
    return p


def run(p, payload):
    commands, unknown = home_commands.parse(payload)
    result = home_commands.Result()
    for command in commands:
        home_commands.apply(p, command, result)
    home_commands.finish(p, result)
    return commands, unknown, result


class CommandTests(unittest.TestCase):
    def setUp(self):
        # Box contents are random; pin them so balances are predictable.
        self.box_items = trophy_road.box_items
        trophy_road.box_items = lambda player, box: [(trophy_road.ITEM_GOLD, None, 50)]

    def tearDown(self):
        trophy_road.box_items = self.box_items

    def test_select_brawler_keeps_its_skin(self):
        p = player()
        commands, unknown, _ = run(p, SELECT_NITA)
        self.assertEqual([c.kind for c in commands], [506, 525])
        self.assertIsNone(unknown)
        self.assertEqual(p['brawler'], 8)
        self.assertEqual(p['skins'], {'8': 14})

    def test_unowned_brawler_cannot_be_selected(self):
        p = player(unlocked=[0])
        run(p, SELECT_NITA)
        self.assertEqual(p['brawler'], 0)

    def test_seen_and_shop_view_parse_without_side_effects(self):
        p = player()
        self.assertEqual(run(p, NITA_SEEN)[1], None)
        self.assertEqual(p['seen'], [8])
        _, unknown, result = run(p, SHOP_OPENED)
        self.assertIsNone(unknown)
        self.assertFalse(result.changed)

    def test_big_box_costs_gems_and_delivers(self):
        p = player()
        _, _, result = run(p, BUY_BIG_BOX)
        self.assertEqual(p['gems'], 70)
        kind, body = result.replies[0]
        self.assertEqual(kind, 24111)
        self.assertEqual([Reader(body).vint() for _ in range(1)], [203])
        p['gems'] = 10
        _, _, result = run(p, BUY_BIG_BOX)
        self.assertEqual(p['gems'], 10)
        self.assertTrue(result.resync)

    def test_token_doubler_and_coin_pack(self):
        p = player()
        run(p, BUY_TOKEN_DOUBLER)
        self.assertEqual((p['gems'], p['token_doubler']), (60, 1500))
        result = home_commands.Result()
        home_commands.apply(p, home_commands.Command(521, [0]), result)
        self.assertEqual((p['gems'], p['gold']), (50, 2000))


class UpgradeTests(unittest.TestCase):
    def test_upgrade_keeps_lifetime_points_and_spends_coins(self):
        p = player(power_points={'8': 42})
        self.assertEqual(brawlers.upgrade(p, 8), 1)
        self.assertEqual((p['power_points']['8'], p['gold']), (42, 980))
        self.assertEqual(brawlers.spare_points(p, 8), 22)
        self.assertIsNone(brawlers.upgrade(p, 8))  # Needs 30 more for power 3.

    def test_points_stop_at_power_nine(self):
        p = player(power_points={'0': brawlers.MAX_POWER_POINTS})
        self.assertEqual(brawlers.points_needed(p, 0), 0)


class ShopTests(unittest.TestCase):
    def test_daily_offers_refresh_once_and_sell_once(self):
        p = player()
        self.assertTrue(shop.daily_offers(p))
        self.assertFalse(shop.daily_offers(p))
        offer = p['offers']['items'][0]
        delivered = shop.buy(p, 0)
        self.assertEqual(delivered, [(6, offer['brawler'], offer['amount'])])
        self.assertEqual(p['gold'], 1000 - offer['cost'])
        self.assertIsNone(shop.buy(p, 0))

    def test_home_data_with_offers_encodes(self):
        p = player(power_points={'0': 18})
        shop.daily_offers(p)
        with_offers = home_data(p)
        p['offers']['items'] = []
        self.assertGreater(len(with_offers), len(home_data(p)))


if __name__ == '__main__':
    unittest.main()
