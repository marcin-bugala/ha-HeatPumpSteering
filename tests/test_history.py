"""History seeding and real Jinja merge, without controlling HA devices."""
import importlib.util
import unittest

from test_memory import ENV, START, as_function, tick, run
from test_poc import ROOT

SPEC = importlib.util.spec_from_file_location(
    'poc_history', ROOT / 'custom_components/hp_poc_history/history.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
reconstruct = MODULE.reconstruct
MERGE = as_function(ENV.get_template('hp_poc_memory.jinja').module.merge_history)
END = START + 15 * 3600


def seed(events=None, runs=None, stamp=END, current=('off', '22.0')):
    if events is None:
        events = [[(START, value)] for value in ('21.5', '22.5', '8', 'off', '22.0')]
    return reconstruct(events, [(START, stamp)] if runs is None else runs, stamp, current)


class HistoryTests(unittest.TestCase):
    def test_one_unchanged_state_covers_whole_window(self):
        result = tick(MERGE({}, seed(), END), END, ground=21.5, upper=22.5,
                      outdoor=8, co1='off', setpoint=22)
        self.assertTrue(result['ground']['ready'])
        self.assertTrue(result['outdoor']['ready'])
        self.assertTrue(result['trend_ground']['ready'])
        self.assertEqual(result['ground']['count'], 37)
        self.assertEqual(result['co1_since'], START)
        self.assertEqual(result['setpoint_since'], START)
        # Past temperatures do not retroactively confirm current goals.
        self.assertEqual(result['hot_seconds'], 0)

    def test_irregular_updates_are_weighted_by_duration(self):
        events = [[(START, value)] for value in ('21', '22', '8', 'off', '22')]
        events[0] += [(END - 600, '23'), (END - 500, '24'), (END - 400, '25')]
        result = tick(MERGE({}, seed(events), END), END, co1='off', setpoint=22)
        self.assertEqual(result['ground']['value'], 21)

    def test_unavailable_interval_is_not_filled(self):
        events = [[(START, value)] for value in ('21', '22', '8', 'off', '22')]
        events[0] += [(END - 3600, 'unavailable'), (END - 300, '21')]
        result = tick(MERGE({}, seed(events), END), END, co1='off', setpoint=22)
        self.assertFalse(result['ground']['ready'])
        self.assertGreater(result['ground']['max_gap'], 1200)
        self.assertTrue(result['upper']['ready'])

    def test_missing_and_bad_history_is_not_zero(self):
        events = [[], [(START, 'nan')], [(START, '99')], [], []]
        result = seed(events)
        self.assertEqual(result['raw'][-1][1:], [None, None, None])
        self.assertIsNone(result['co1_since'])
        self.assertIsNone(result['setpoint_since'])

    def test_switch_transitions_unknown_and_repeated_reports(self):
        events = [[(START, value)] for value in ('21', '22', '8', 'off', '22')]
        events[3] += [(END - 7200, 'on'), (END - 6000, 'on'),
                      (END - 5000, 'unknown'), (END - 4000, 'off'), (END - 200, 'off')]
        events[4] += [(END - 8000, '23.0'), (END - 4000, '22'), (END - 200, '22.0')]
        result = seed(events)
        self.assertEqual(result['co1_since'], END - 4000)
        self.assertEqual(result['setpoint_since'], END - 4000)

    def test_current_state_mismatch_does_not_recover_timer(self):
        result = seed(current=('on', '23'))
        self.assertIsNone(result['co1_since'])
        self.assertIsNone(result['setpoint_since'])

    def test_long_ha_outage_breaks_samples_and_state_continuity(self):
        runs = [(START, END - 7200), (END - 1800, END)]
        result = seed(runs=runs)
        self.assertEqual(result['co1_since'], END - 1800)
        self.assertTrue(any(row[1] is None for row in result['raw']))
        memory = tick(MERGE({}, result, END), END, co1='off', setpoint=22)
        self.assertFalse(memory['ground']['ready'])

    def test_short_restart_keeps_timer_but_not_offline_samples(self):
        result = seed(runs=[(START, END - 1800), (END - 1200, END)])
        self.assertEqual(result['co1_since'], START)
        self.assertIsNone(next(row[1] for row in result['raw'] if row[0] == END - 1500))

    def test_no_uptime_evidence_before_current_run_does_not_recover_old_timer(self):
        result = seed(runs=[(END - 600, END)])
        self.assertEqual(result['co1_since'], END - 600)

    def test_no_recorder_runs_cannot_establish_readiness(self):
        result = seed(runs=[])
        self.assertTrue(all(row[1] is None for row in result['raw']))
        self.assertIsNone(result['co1_since'])

    def test_recent_live_samples_take_precedence(self):
        live = run()
        result = MERGE(live, seed(stamp=live['updated']), live['updated'])
        self.assertEqual(result['raw'][-1][1], live['raw'][-1][1])
        invalid = tick(live, live['updated'] + 300, ground=None)
        result = MERGE(invalid, seed(stamp=invalid['updated']), invalid['updated'])
        self.assertIsNone(result['raw'][-1][1])

    def test_history_fills_unready_trend_without_duplicating_buckets(self):
        live = tick({}, END - 300, co1='off', setpoint=22)
        self.assertIsNone(live['trend'][0][1])
        merged = MERGE(live, seed(), END)
        self.assertTrue(all(row[1] is not None for row in merged['trend']))
        self.assertEqual(len(merged['trend']), 145)
        self.assertEqual(len({row[0] // 300 for row in merged['raw']}), len(merged['raw']))

    def test_query_race_never_restores_a_timer_past_live_change(self):
        live = tick({}, END + 1, co1='on', setpoint=23)
        merged = MERGE(live, seed(), END + 1)
        self.assertEqual(merged['co1'], 'on')
        self.assertEqual(merged['co1_since'], END + 1)
        self.assertEqual(merged['setpoint_since'], END + 1)

    def test_stale_and_future_events_are_ignored(self):
        live = run()
        for generated in (live['updated'] - 121, live['updated'] + 1):
            history = seed(stamp=generated)
            self.assertEqual(MERGE(live, history, live['updated']), live)

    def test_second_refresh_is_idempotent_and_memory_stays_bounded(self):
        live = tick(MERGE({}, seed(), END), END, co1='off', setpoint=22)
        merged = MERGE(live, seed(), END)
        self.assertEqual(merged['raw'], live['raw'])
        self.assertEqual(merged['trend'], live['trend'])
        import json
        self.assertLess(len(json.dumps(merged)), 16384)


if __name__ == '__main__':
    unittest.main()
