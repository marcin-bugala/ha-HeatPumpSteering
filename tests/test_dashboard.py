"""Checks the delivered dashboard templates, layout and read-only boundaries."""
import unittest
import yaml
from test_poc import ROOT, Harness, State, fixture

DASHBOARD_PATH = next(p for p in [
    ROOT / 'home-assistant/dashboards/dashboard_historia.yaml',
    ROOT.parents[1] / 'home-assistant/dashboards/dashboard_historia.yaml',
] if p.exists())
DASHBOARD = yaml.safe_load(DASHBOARD_PATH.read_text(encoding='utf-8'))
POC_VIEW = next(view for view in DASHBOARD['views'] if view.get('path') == 'co1')


def cards(value):
    if isinstance(value, dict):
        if 'type' in value:
            yield value
        for child in value.values():
            yield from cards(child)
    elif isinstance(value, list):
        for child in value:
            yield from cards(child)


class DashboardTests(unittest.TestCase):
    def test_columns_and_controls(self):
        view = POC_VIEW
        self.assertEqual(view['type'], 'sections')
        self.assertEqual(view['max_columns'], 3)
        left, middle, right = view['sections']
        self.assertEqual(len(list(c for c in cards(left) if c['type'] == 'history-graph')), 5)
        self.assertEqual(len(list(c for c in cards(left) if c['type'] == 'custom:hp-poc-readonly-card')), 1)
        for section in [left, right]:
            self.assertFalse(any(c['type'] in ['tile', 'entities'] for c in cards(section)))
        self.assertEqual(len(list(c for c in cards(middle) if c['type'] == 'tile')), 3)
        for c in cards(DASHBOARD):
            if c['type'] == 'history-graph':
                self.assertTrue(all(isinstance(e, dict) and e.get('name') for e in c['entities']))

    def test_markdown_handles_ready_missing_and_empty_data(self):
        for scenario in ['ready', 'missing', 'empty']:
            with self.subTest(scenario=scenario):
                data = fixture() if scenario != 'empty' else {}
                harness = Harness(data)
                if scenario == 'ready': harness.decision()
                data['sensor.hp_poc_status'] = State('sensor.hp_poc_status', 'brak_encji',
                    {'missing_entities': ['sensor.hp_poc_parter_komfort'] if scenario == 'missing' else []})
                for card in cards(POC_VIEW):
                    if card['type'] == 'markdown':
                        output = harness.render(card['content'], {})
                        self.assertIsInstance(output, str)
                        self.assertNotIn('None °C', output)
                        self.assertNotIn('hp_poc_parter_komfort 23', output)


if __name__ == '__main__':
    unittest.main()
