"""Replay observational filters, confirmation clocks, outages and conflicts."""
import json
import unittest
from copy import deepcopy
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from test_memory import as_function, run, tick
from test_poc import ROOT, numeric

ENV = Environment(loader=FileSystemLoader(ROOT/'templates'), undefined=StrictUndefined,
                  extensions=['jinja2.ext.do'])
ENV.globals.update(is_number=numeric,
    state_attr=lambda entity, key: {'min':20, 'max':35}.get(key))
ENV.filters['as_function'] = as_function
OBSERVE = as_function(ENV.get_template('shadow_observation.jinja').module.observe)


def observe(p, old=None, stamp=None, fresh=True, valid=True, enabled=True, actual='off',
            goals=(21,22), live=None, last_try=0):
    live = live or p['raw'][-1][1:3]
    return OBSERVE(p,old or {},p['updated'] if stamp is None else stamp,*goals,*live,
                   fresh,valid,enabled,actual,last_try)


class ShadowTests(unittest.TestCase):
    def test_constant_history_ready_immediately_without_faking_confirmation(self):
        p = run(ground=20, upper=21, co1='off')
        result = observe(p)
        self.assertEqual(result['data']['gf'],20)
        self.assertEqual(result['data']['g2'],20)
        self.assertEqual(result['data']['dg'],0)
        self.assertEqual(result['data']['q'],'confirm')
        self.assertEqual(result['clock']['c'],0)

    def test_thirty_real_minutes_confirm_start_but_no_device_action(self):
        p = run(ground=20, upper=21, co1='off')
        old = observe(p)['clock']
        for _ in range(6):
            p = tick(p,p['updated']+300,ground=20,upper=21,co1='off')
            result = observe(p,old)
            old = result['clock']
        self.assertEqual(result['data']['c'],1800)
        self.assertEqual(result['data']['q'],'start')

    def test_co1_minimum_time_and_retry_block_advice(self):
        p = run(ground=20, upper=21, co1='off')
        old = dict(t=p['updated']-300,g=21,u=22,h=0,c=1800,hv=False,cv=True)
        p['co1_since'] = p['updated']-300
        self.assertEqual(observe(p,old)['data']['q'],'lock')
        p['co1_since'] = p['updated']-10000
        self.assertEqual(observe(p,old,last_try=p['updated']-100)['data']['q'],'lock')

    def test_both_floors_required_for_stop(self):
        p = run(ground=22, upper=22.2)
        self.assertEqual(observe(p,actual='on')['data']['q'],'hold')
        p = run(ground=22, upper=23)
        old = dict(t=p['updated']-300,g=21,u=22,h=1800,c=0,hv=True,cv=False)
        self.assertEqual(observe(p,old,actual='on')['data']['q'],'stop')

    def test_ventilation_blocks_start(self):
        p = run(ground=20,upper=21,co1='off')
        old = dict(t=p['updated']-300,g=21,u=22,h=0,c=1800,hv=False,cv=True)
        result = observe(p,old,live=(18,21))
        self.assertEqual(result['data']['c'],0)
        self.assertEqual(result['data']['q'],'hold')

    def test_goal_change_resets_confirmation(self):
        p = run(ground=20,upper=21,co1='off')
        old = dict(t=p['updated']-300,g=21,u=22,h=0,c=1800,hv=False,cv=True)
        self.assertEqual(observe(p,old,goals=(21.1,22))['clock']['c'],0)

    def test_repeated_evaluation_does_not_inflate_clock(self):
        p = run(ground=20,upper=21,co1='off')
        old = dict(t=p['updated'],g=21,u=22,h=0,c=600,hv=False,cv=True)
        result = observe(p,old,stamp=p['updated']+20)
        self.assertEqual(result['clock']['c'],600)

    def test_short_restart_pauses_long_restart_resets(self):
        p = run(ground=20,upper=21,co1='off')
        old = dict(t=p['updated']-600,g=21,u=22,h=0,c=600,hv=False,cv=True)
        self.assertEqual(observe(p,old)['clock']['c'],600)
        old['t'] = p['updated']-1500
        self.assertEqual(observe(p,old)['clock']['c'],0)

    def test_invalid_last_sample_and_stale_memory_never_produce_ready_advice(self):
        p = run()
        for version in ('latest','stale','source'):
            data = deepcopy(p)
            if version == 'latest': data['raw'][-1][1] = None
            result = observe(data,stamp=p['updated']+700 if version=='stale' else None,
                             fresh=version!='source',live=(21,22))
            self.assertIsNone(result['data']['gf'])
            self.assertEqual(result['data']['q'],'data')

    def test_fast_filter_follows_change_before_two_hour_median(self):
        p = run(ground=21,upper=22)
        for row in p['raw'][-10:]: row[1] = 23
        result = observe(p)
        self.assertEqual(result['data']['gf'],23)
        self.assertEqual(result['data']['g2'],21)

    def test_short_trend_rejects_unobserved_gap_between_endpoints(self):
        p = run()
        for row in p['raw']:
            if p['updated']-5100 <= row[0] <= p['updated']-2400:
                row[1] = None
        self.assertIsNone(observe(p)['data']['dg'])

    def test_short_trend_disables_old_warming_penalty_when_temperature_falls(self):
        p = run(ground=21,upper=22)
        p['outdoor']['average'] = -4
        p['trend_ground'] = dict(ready=True,change=1)
        p['trend_upper'] = dict(ready=True,change=0)
        for row in p['raw']:
            row[1] = 21+(p['updated']-row[0])/10800
        result = observe(p)
        self.assertLess(result['data']['dg'],0)
        self.assertEqual(result['data']['c3'],25)

    def test_disabled_and_unknown_co1_are_not_actionable(self):
        p = run()
        self.assertEqual(observe(p,enabled=False)['data']['q'],'disabled')
        self.assertEqual(observe(p,actual='unknown')['data']['q'],'data')

    def test_snapshot_fits_native_helper_and_does_not_mutate_live_memory(self):
        p = run()
        before = deepcopy(p)
        result = observe(p)
        for item in result.values(): self.assertLess(len(json.dumps(item)),256)
        self.assertEqual(before,p)

    def test_deployment_only_writes_observation_helpers(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('shadow_builder',ROOT/'tools/build_shadow.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        automation = builder.build()['automation']
        for action in automation['actions'][1:]:
            self.assertEqual(action['action'],'input_text.set_value')
            self.assertTrue(action['target']['entity_id'].startswith('input_text.hp_poc_porownanie_'))


if __name__ == '__main__': unittest.main()
