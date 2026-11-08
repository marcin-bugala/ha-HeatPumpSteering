"""Replay real memory macros over hours, restarts and gaps; no HA writes."""
import json
import unittest
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from test_poc import ROOT, numeric, PACKAGE, Harness, fixture, State, NOW


def as_function(macro):
    def call(*args, **kwargs):
        result = []
        macro(*args, **kwargs, returns=result.append)
        return result[0]
    return call


ENV = Environment(loader=FileSystemLoader(ROOT / 'custom_templates'),
                  undefined=StrictUndefined, extensions=['jinja2.ext.do'])
ENV.globals.update(is_number=numeric)
ENV.filters['as_function'] = as_function
NEXT = as_function(ENV.get_template('hp_poc_memory.jinja').module.next_memory)
START = 1794000000 // 300 * 300


def tick(previous, stamp, ground=21.0, upper=22.0, outdoor=-5.0, co1='on', setpoint=25):
    return NEXT(previous, stamp, ground, upper, outdoor, 21.0, 22.0, co1, setpoint)


def run(hours=3, ground=21, upper=22, co1='on'):
    p = {}
    for offset in range(0, hours * 3600 + 1, 300):
        p = tick(p, START + offset, ground, upper, co1=co1)
    return p


class MemoryTests(unittest.TestCase):
    def test_constant_values_are_full_samples(self):
        p = run()
        self.assertTrue(p['ground']['ready'])
        self.assertEqual(p['ground']['count'], 37)
        self.assertEqual(p['outdoor']['count'], 25)
        self.assertEqual(p['ground']['value'], 21)
        self.assertEqual(p['outdoor']['average'], -5)

    def test_restore_equal_to_uninterrupted_run(self):
        p = run()
        restored = json.loads(json.dumps(p))  # native restore uses JSON
        now = START + 3 * 3600 + 300
        self.assertEqual(tick(p, now), tick(restored, now))
        after = tick(restored, now)
        self.assertTrue(after['ground']['ready'])
        self.assertEqual(after['co1_since'], p['co1_since'])
        self.assertEqual(after['setpoint_since'], p['setpoint_since'])

    def test_short_restart_missing_one_sample(self):
        p = run()
        after = tick(json.loads(json.dumps(p)), START + 3 * 3600 + 600)
        self.assertTrue(after['ground']['ready'])
        self.assertEqual(after['ground']['max_gap'], 600)
        self.assertEqual(after['co1_since'], p['co1_since'])

    def test_long_gap_blocks_readiness_and_resets_uncertain_transition(self):
        p = run()
        after = tick(p, START + 4 * 3600)
        self.assertFalse(after['ground']['ready'])
        self.assertEqual(after['ground']['max_gap'], 3600)
        self.assertEqual(after['co1_since'], after['updated'])

    def test_loss_of_recent_checkpoint_does_not_require_three_hour_warmup(self):
        checkpoint = run()
        after = tick(json.loads(json.dumps(checkpoint)), checkpoint['updated'] + 900)
        self.assertTrue(after['ground']['ready'])
        self.assertTrue(after['outdoor']['ready'])
        self.assertEqual(after['co1_since'], checkpoint['co1_since'])

    def test_target_change_restarts_confirmation_not_temperature_history(self):
        p = run(ground=22, upper=23)
        self.assertEqual(p['hot_seconds'], 1800)
        after = NEXT(p, p['updated'] + 300, 22, 23, -5, 20.5, 21.5, 'on', 25)
        self.assertEqual(after['hot_seconds'], 0)
        self.assertTrue(after['ground']['ready'])

    def test_state_events_do_not_inflate_count(self):
        p = run()
        count = p['ground']['count']
        after = tick(p, p['updated'] + 20, setpoint=24)
        self.assertLessEqual(after['ground']['count'], count)  # oldest may expire
        self.assertEqual(after['raw'][-1][0], p['raw'][-1][0])
        self.assertEqual(after['setpoint_since'], after['updated'])
        self.assertEqual(after['co1_since'], p['co1_since'])

    def test_confirmation_pauses_over_restart(self):
        p = run(ground=22, upper=23)
        p['hot_seconds'] = 1200
        after = tick(p, p['updated'] + 600, ground=22, upper=23)
        self.assertEqual(after['hot_seconds'], 1200)  # offline 10 min not counted
        after = tick(after, after['updated'] + 300, ground=22, upper=23)
        self.assertEqual(after['hot_seconds'], 1500)
        after = tick(after, after['updated'] + 300, ground=22, upper=23)
        self.assertEqual(after['hot_seconds'], 1800)

    def test_ventilation_blocks_cold_confirmation(self):
        p = run(ground=20, upper=21)
        self.assertEqual(p['cold_seconds'], 1800)
        after = tick(p, p['updated'] + 300, ground=17, upper=21)
        self.assertEqual(after['cold_seconds'], 0)

    def test_unknown_does_not_create_zero_temperature(self):
        p = run()
        after = tick(p, p['updated'] + 300, ground=None, upper=None, outdoor=None, co1='unknown', setpoint=None)
        self.assertIsNone(after['raw'][-1][1])
        self.assertEqual(after['ground']['value'], 21)
        self.assertEqual(after['co1_since'], p['co1_since'])

    def test_cold_start_and_clock_backwards(self):
        p = tick({}, START)
        self.assertFalse(p['ground']['ready'])
        p = run()
        p = tick(p, START - 300)
        self.assertFalse(p['ground']['ready'])
        self.assertEqual(p['co1_since'], START - 300)

    def test_history_and_payload_size_bounded_after_two_days(self):
        p = run(hours=48)
        self.assertEqual(len(p['raw']), 37)
        self.assertEqual(len(p['trend']), 145)
        self.assertTrue(p['trend_ground']['ready'])
        self.assertLess(len(json.dumps({'payload': p}).encode()), 16384)

    def test_memory_package_templates_compile_and_empty_proxies_are_safe(self):
        config = yaml.safe_load((ROOT / 'packages/heat_pump_steering_memory.yaml').read_text(encoding='utf-8'))
        harness = Harness(fixture())
        harness.data.pop('sensor.hp_poc_pamiec', None)
        for sensor in config['template'][1]['sensor']:
            self.assertFalse(harness.render(sensor['availability'], {}))
            harness.render(sensor['state'], {})
            for template in sensor['attributes'].values():
                harness.render(template, {})
        harness.data['sensor.hp_poc_pamiec'] = State('sensor.hp_poc_pamiec', NOW.timestamp(), {'payload': {}})
        for sensor in config['template'][1]['sensor']:
            harness.render(sensor['state'], {})

    def test_control_consumers_use_persistent_filters(self):
        consumers = json.dumps([PACKAGE['template'], PACKAGE['automation']])
        for name in ['parter_komfort', 'pietro_komfort', 'outdoor_2h',
                     'parter_liczba_probek', 'pietro_liczba_probek', 'outdoor_liczba_probek',
                     'parter_zmiana_12h', 'pietro_zmiana_12h']:
            self.assertIn('sensor.hp_poc_' + name + '_trwaly', consumers)
            self.assertNotIn('sensor.hp_poc_' + name + "'", consumers)


if __name__ == '__main__':
    unittest.main()
