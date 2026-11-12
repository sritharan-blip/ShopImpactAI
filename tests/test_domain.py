import ast
from datetime import date, timedelta
import io
import json
from pathlib import Path
import unittest

from shopimpact.catalog import CATEGORIES, PRODUCTS
from shopimpact.data import _make_data_backup, _parse_data_backup, _parse_purchase_csv
from shopimpact.logic import (_new_purchase, _new_wishlist_item, calculate_impact,
                              check_badges, _cart_totals, _product_impact,
                              _month_end_forecast, _month_end_spend_forecast)
from shopimpact.recommendations import recommend_products
from shopimpact.theme import PALETTES
from shopimpact.decisions import decision_projection


class DomainTests(unittest.TestCase):
    def purchase(self, **kwargs):
        return _new_purchase('Phone', 'Electronics', 'Demo', 329, date.today(), **kwargs)

    def test_category_estimate_validation(self):
        self.assertEqual(calculate_impact('Electronics', 329), 115.15)
        for amount in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                calculate_impact('Electronics', amount)
        with self.assertRaises(ValueError):
            calculate_impact('Unknown', 10)

    def test_catalog_snapshot_reduction_units(self):
        purchase = self.purchase(co2_override=51)
        self.assertEqual(purchase['carbon_saved_kg'], 64.15)
        self.assertEqual(purchase['baseline_co2'], 115.15)
        self.assertEqual(purchase['co2'], 51)
        badges = check_badges([purchase])['badges']
        saver = next(b for b in badges if b['key'] == 'saver')
        self.assertTrue(saver['earned'])
        self.assertIn('kg CO2e', saver['description'])
        self.assertNotIn('$', saver['description'])

    def test_lossless_backup_with_catalog_estimate_and_wishlist(self):
        purchase = self.purchase(co2_override=51)
        wish = _new_wishlist_item('Lamp', 'Home & living', 'Demo', 30, date.today(), 'Need', 'Keep it')
        restored, issues = _parse_data_backup(io.BytesIO(_make_data_backup([purchase], [wish])))
        self.assertEqual(issues, [])
        self.assertEqual(restored, {'purchases': [purchase], 'wishlist': [wish]})

    def test_backup_keeps_historical_baseline_when_factors_change(self):
        purchase = self.purchase(co2_override=51)
        data = _make_data_backup([purchase], [])
        old = CATEGORIES['Electronics']['factor']
        try:
            CATEGORIES['Electronics']['factor'] = 9
            restored, issues = _parse_data_backup(io.BytesIO(data))
            self.assertEqual(issues, [])
            self.assertEqual(restored['purchases'][0], purchase)
        finally:
            CATEGORIES['Electronics']['factor'] = old

    def test_legacy_backup_keeps_co2_ignores_ambiguous_money(self):
        old = self.purchase(co2_override=51)
        for key in ['carbon_saved_kg', 'baseline_co2', 'estimate_method']:
            old.pop(key)
        old['green_savings'] = 99999
        payload = {'schema_version': 1, 'purchases': [old], 'wishlist': []}
        restored, issues = _parse_data_backup(io.BytesIO(json.dumps(payload).encode()))
        self.assertEqual(issues, [])
        self.assertEqual(restored['purchases'][0]['co2'], 51)
        self.assertEqual(restored['purchases'][0]['carbon_saved_kg'], 64.15)

    def test_invalid_backup_is_atomic(self):
        valid = self.purchase()
        for change in [{'price': 'NaN'}, {'co2': -1}, {'date': '2999-01-01'},
                       {'carbon_saved_kg': 999}, {'product': None}, {'price': [1]},
                       {'co2': True}, {'category': 'Bad'}]:
            with self.subTest(change=change):
                invalid = {**valid, **change, 'id': 'other'}
                payload = {'schema_version': 2, 'purchases': [valid, invalid], 'wishlist': []}
                result, errors = _parse_data_backup(io.BytesIO(json.dumps(payload).encode()))
                self.assertIsNone(result)
                self.assertTrue(errors)

    def test_backup_duplicate_ids_and_size(self):
        p = self.purchase()
        result, errors = _parse_data_backup(io.BytesIO(_make_data_backup([p, p], [])))
        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertIsNone(_parse_data_backup(io.BytesIO(b' ' * (5 * 1024 * 1024 + 1)))[0])

    def test_csv_valid_rows_only_and_recalculate(self):
        data = b'product,category,price,date,co2\nPhone,Electronics,100,,0\nBad,Electronics,NaN,,0\nFuture,Electronics,10,2999-01-01,0\n'
        rows, issues = _parse_purchase_csv(io.BytesIO(data))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['co2'], 35)
        self.assertEqual(len(issues), 2)

    def test_csv_duplicate_headers_and_row_limit(self):
        self.assertTrue(_parse_purchase_csv(io.BytesIO(b'product,category,price, PRICE\na,Electronics,1,2'))[1])
        rows, issues = _parse_purchase_csv(io.BytesIO(('product,category,price\n' + 'a,Electronics,1\n' * 5001).encode()))
        self.assertEqual(rows, [])
        self.assertTrue(issues)

    def test_cart_quantities_and_shipping(self):
        product = PRODUCTS[0]
        self.assertEqual(_cart_totals({})['total'], 0)
        self.assertEqual(_cart_totals({product['id']: 2})['estimated_co2'], _product_impact(product, 2))
        self.assertEqual(_cart_totals({'repair-kit': 1})['shipping'], 4.95)

    def test_recommendations_intent_budget_category(self):
        rows = recommend_products('repairable modular laptop', budget=800)
        self.assertEqual(rows[0]['id'], 'modular-laptop')
        rows = recommend_products('phone', category='Electronics', budget=400)
        self.assertEqual([r['id'] for r in rows], ['refurb-phone'])
        self.assertTrue(all(r['reasons'] for r in rows))
        self.assertEqual(recommend_products('laptop', category='Electronics', budget=10), [])

    def test_personalization_opt_out(self):
        self.assertEqual(recommend_products(purchases=[self.purchase()], personalize=False),
                         recommend_products(purchases=[], personalize=False))

    def test_forecasts_month_end_and_leap_year(self):
        last = date(2024, 2, 29)
        self.assertEqual(_month_end_forecast(10, last, 25)['days_remaining'], 0)
        self.assertEqual(_month_end_forecast(10, last, 25)['daily_allowance'], 0)
        self.assertEqual(_month_end_spend_forecast(100, date(2024, 2, 1), 1000)['projected_spend'], 2900)

    def test_python_310_grammar(self):
        root = Path(__file__).resolve().parents[1]
        for path in [root / 'ShopImpactAI.py', *(root / 'shopimpact').glob('*.py')]:
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 10))

    def test_theme_text_contrast(self):
        def luminance(color):
            values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
            return sum(a * b for a, b in zip(linear, [.2126, .7152, .0722]))
        for mode, palette in PALETTES.items():
            for fg, bg in [('text', 'page'), ('muted', 'page'), ('text', 'surface'),
                           ('muted', 'surface'), ('text', 'inset'), ('accent_text', 'accent')]:
                with self.subTest(mode=mode, foreground=fg, background=bg):
                    a, b = sorted([luminance(palette[fg]), luminance(palette[bg])])
                    self.assertGreaterEqual((b + .05) / (a + .05), 4.5)

    def test_cost_per_use_and_budget(self):
        self.assertEqual(decision_projection(120, 3, 2, 200, 600),
                         {'uses': 312, 'cost_per_use': .38, 'remaining': 280, 'budget_share': 20})
        self.assertEqual(decision_projection(200, 1, 1, 500, 600)['remaining'], -100)

    def test_decision_model_invalid_assumptions(self):
        for values in [(120, 0, 2), (-1, 3, 2), (120, 3, 0), (float('nan'), 3, 2), (120, float('inf'), 2)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                decision_projection(*values)


if __name__ == '__main__':
    unittest.main()
