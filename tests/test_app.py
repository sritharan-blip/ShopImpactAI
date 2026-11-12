from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ENTRY = str(Path(__file__).resolve().parents[1] / 'ShopImpactAI.py')
VIEWS = ['Overview', 'Discover', 'Decision lab', 'Log purchase', 'Wishlist', 'Cart & checkout',
         'My orders', 'Impact analytics', 'Swap studio', 'Eco rewards', 'Help & returns', 'Profile']


class AppTests(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(ENTRY, default_timeout=30).run()
        self.assertEqual(list(app.exception), [])
        return app

    def test_all_views_in_both_themes(self):
        app = self.app()
        app.button(key='load_demo').click().run()
        for mode in ['Daylight', 'Midnight']:
            app.session_state['appearance'] = mode
            for view in VIEWS:
                with self.subTest(mode=mode, view=view):
                    app.radio(key='view').set_value(view).run()
                    self.assertEqual(list(app.exception), [])
                    self.assertEqual(app.session_state['dark_mode'], mode == 'Midnight')

    def test_checkout_and_ledger_snapshot(self):
        app = self.app()
        app.session_state['profile'] = {'name': 'Test Shopper', 'email': 'test@example.com', 'personalization': True}
        app.session_state['cart'] = {'refurb-phone': 2}
        app.radio(key='view').set_value('Cart & checkout').run()
        app.text_input(key='checkout_city').set_value('Demo city')
        app.text_input(key='checkout_postal').set_value('000000')
        next(c for c in app.checkbox if c.label == 'I understand this is a non-binding demo order.').check()
        next(b for b in app.button if b.label == 'Place demo order').click().run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(len(app.session_state['orders']), 1)
        purchase = app.session_state['purchases'][0]
        self.assertEqual(purchase['co2'], 101.99)
        self.assertEqual(purchase['carbon_saved_kg'], 128.31)
        self.assertEqual(app.session_state['view'], 'My orders')

    def test_manual_green_scenario_and_literal_search(self):
        app = self.app()
        app.radio(key='view').set_value('Log purchase').run()
        app.text_input(key='log_product').set_value('Phone [refurbished]')
        app.selectbox(key='log_category').set_value('Electronics')
        app.number_input(key='log_price').set_value(100)
        app.checkbox(key='log_green_choice').check()
        next(b for b in app.button if b.label == 'Add to my impact log').click().run()
        self.assertEqual(list(app.exception), [])
        purchase = app.session_state['purchases'][0]
        self.assertEqual(purchase['co2'], 4)
        self.assertEqual(purchase['carbon_saved_kg'], 31)
        app.text_input(key='history_search').set_value('[').run()
        self.assertEqual(list(app.exception), [])

    def test_empty_views(self):
        app = self.app()
        for view in VIEWS:
            with self.subTest(view=view):
                app.radio(key='view').set_value(view).run()
                self.assertEqual(list(app.exception), [])

    def test_theme_switches_preserve_data_and_accessibility(self):
        app = self.app()
        app.button(key='load_demo').click().run()
        before = list(app.session_state['purchases'])
        for mode in ['Midnight', 'Daylight', 'Midnight']:
            app.session_state['appearance'] = mode
            app.run()
            self.assertEqual(app.session_state['dark_mode'], mode == 'Midnight')
            self.assertEqual(app.session_state['purchases'], before)
        app.toggle(key='reduce_motion').set_value(True).run()
        app.toggle(key='high_contrast').set_value(True).run()
        self.assertEqual(list(app.exception), [])
        self.assertTrue(app.session_state['reduce_motion'])
        self.assertTrue(app.session_state['high_contrast'])

    def test_decision_lab_saves_a_pause_plan(self):
        app = self.app()
        app.radio(key='view').set_value('Decision lab').run()
        app.text_input(key='decision_product').set_value('Headphones')
        app.button(key='save_decision').click().run()
        self.assertEqual(list(app.exception), [])
        item = app.session_state['wishlist'][0]
        self.assertEqual(item['product'], 'Headphones')
        self.assertIn('Decision lab', item['note'])
        self.assertGreater(date.fromisoformat(item['revisit_on']), date.today())


if __name__ == '__main__':
    unittest.main()
