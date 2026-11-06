"""Exercise the actual YAML/Jinja algorithm offline; no connection to HA."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
import math
import ast
import unittest

import yaml
from jinja2 import Environment, StrictUndefined, Undefined
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = yaml.safe_load((ROOT / 'packages/heat_pump_steering_poc.yaml').read_text(encoding='utf-8'))
NOW = datetime(2026, 11, 6, 20, tzinfo=timezone.utc)
CO1 = 'number.garaz_pompa_ciepla_circuit_1_setpoint'
PROPOSAL = 'sensor.hp_poc_co1_propozycja'


class State:
    def __init__(self, entity, value, attrs=None, age=0, changed=10000):
        self.entity_id = entity
        self.state = str(value)
        self.attributes = attrs or {}
        self.last_reported = NOW - timedelta(seconds=age)
        self.last_changed = NOW - timedelta(seconds=changed)


class States:
    def __init__(self, data, prefix=''):
        self.data, self.prefix = data, prefix

    def __call__(self, entity):
        return self.data[entity].state if entity in self.data else 'unknown'

    def __getattr__(self, key):
        entity = self.prefix + key
        if not self.prefix:
            return States(self.data, entity + '.')
        return self.data.get(entity, Undefined(name=entity))

    def __getitem__(self, entity):
        return self.data.get(entity, Undefined(name=entity))

    def __iter__(self):
        return iter(self.data.values())


def timestamp(value, default=0):
    try:
        return value.timestamp() if isinstance(value, datetime) else datetime.fromisoformat(value).timestamp()
    except (ValueError, TypeError):
        return default


def numeric(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def fixture(ground=21, upper=22, outdoor=-5, current=28):
    values = {
        'sensor.salon_termometr_salon': ground,
        'sensor.korytarz_termometr_pietro': upper,
        'sensor.garaz_pompa_ciepla_outdoor_ambient_temp': outdoor,
        'sensor.garaz_pompa_ciepla_circuit_1_water_temp': 28,
        'sensor.hp_poc_probka_parter': ground,
        'sensor.hp_poc_probka_pietro': upper,
        'sensor.hp_poc_probka_outdoor': outdoor,
        'sensor.hp_poc_parter_komfort': ground,
        'sensor.hp_poc_pietro_komfort': upper,
        'sensor.hp_poc_outdoor_2h': outdoor,
        'sensor.hp_poc_parter_zmiana_12h': 0,
        'sensor.hp_poc_pietro_zmiana_12h': 0,
        'sensor.hp_poc_parter_liczba_probek': 36,
        'sensor.hp_poc_pietro_liczba_probek': 36,
        'sensor.hp_poc_outdoor_liczba_probek': 24,
        'input_number.hp_poc_cel_parter': 21,
        'input_number.hp_poc_cel_pietro': 22,
        'input_boolean.hp_poc_cele_zainicjalizowane': 'on',
        'input_datetime.hp_poc_ostatnia_proba': '2026-11-05 00:00:00+00:00',
        'switch.garaz_pompa_ciepla_circuit_1_heating': 'on',
        CO1: current,
    }
    data = {key: State(key, value, {'age_coverage_ratio': 0.95}) for key, value in values.items()}
    data[CO1].attributes = {'min': 27, 'max': 55, 'step': 1, 'unit_of_measurement': '°C'}
    return data


class Harness:
    def __init__(self, data):
        self.data = data
        states = States(data)
        self.env = Environment(undefined=StrictUndefined)
        self.env.globals.update(states=states, now=lambda: NOW, as_timestamp=timestamp,
                                is_number=numeric, is_state=lambda e, s: states(e) == s,
                                state_attr=lambda e, a: data[e].attributes.get(a) if e in data else None)

    def render(self, value, variables):
        if not isinstance(value, str) or not ('{{' in value or '{%' in value):
            return value
        result = self.env.from_string(value).render(**variables).strip()
        try:
            return ast.literal_eval(result)
        except (ValueError, SyntaxError):
            return result

    def variables(self, steps, variables):
        for step in steps:
            if 'variables' in step:
                for key, value in step['variables'].items():
                    variables[key] = self.render(value, variables)
        return variables

    def decision(self):
        block = next(block for block in PACKAGE['template'] if 'actions' in block)
        variables = self.variables(block['actions'], {})
        entity = block['sensor'][0]
        attrs = {k: self.render(v, variables) for k, v in entity['attributes'].items()}
        self.data[PROPOSAL] = State(PROPOSAL, variables['rounded'] if variables['ready'] else 'unavailable', attrs)
        return variables

    def write_allowed(self):
        automation = PACKAGE['automation'][1]
        variables = deepcopy(automation['variables'])
        if not self.render(automation['conditions'][0]['value_template'], variables):
            return False
        self.variables(automation['actions'][:2], variables)
        return bool(self.render(automation['actions'][2]['value_template'], variables))


class PocTests(unittest.TestCase):
    def test_templates_compile(self):
        def walk(value):
            if isinstance(value, dict):
                for child in value.values(): walk(child)
            elif isinstance(value, list):
                for child in value: walk(child)
            elif isinstance(value, str) and ('{{' in value or '{%' in value):
                NativeEnvironment().parse(value)
        walk(PACKAGE)
        walk(yaml.safe_load((ROOT / 'dashboards/heating_poc.yaml').read_text(encoding='utf-8')))

    def test_overheating_and_minimum(self):
        harness = Harness(fixture(23.5, 22.9))
        result = harness.decision()
        self.assertTrue(result['ready'])
        self.assertEqual(result['correction'], -2)
        self.assertEqual(result['rounded'], 27)
        self.assertTrue(harness.write_allowed())

    def test_same_integer_never_writes(self):
        harness = Harness(fixture(current=27))
        harness.decision()
        self.assertFalse(harness.write_allowed())

    def test_half_up_rounding(self):
        harness = Harness(fixture(outdoor=-17.5, current=28))
        self.assertEqual(harness.decision()['rounded'], 28)
        self.assertFalse(harness.write_allowed())

    def test_cold_house_one_degree_step(self):
        harness = Harness(fixture(19, 20, -20, current=27))
        self.assertEqual(harness.decision()['rounded'], 30)
        self.assertTrue(harness.write_allowed())
        auto = PACKAGE['automation'][1]
        variables = harness.variables(auto['actions'][:2], deepcopy(auto['variables']))
        self.assertEqual(variables['next_value'], 28)

    def test_conflicting_floors_prioritize_overheating(self):
        result = Harness(fixture(22, 20, -20)).decision()
        self.assertLess(result['correction'], 0)

    def test_short_spike_and_ventilation(self):
        # Regular 5-min sampling: 30-min excursion cannot move the 3h median.
        self.assertEqual(median([21] * 30 + [24] * 6), 21)
        self.assertEqual(median([21] * 30 + [17] * 6), 21)
        data = fixture(19, 20, -20, 27)
        data['sensor.hp_poc_probka_parter'].state = '17'
        harness = Harness(data)
        self.assertTrue(harness.decision()['block_increase'])
        self.assertFalse(harness.write_allowed())

    def test_sustained_heat_is_not_discarded(self):
        self.assertEqual(median([21] * 10 + [23] * 26), 23)

    def test_rising_trend_reduces_target(self):
        data = fixture(outdoor=-20)
        data['sensor.hp_poc_parter_zmiana_12h'].state = '1.15'
        result = Harness(data).decision()
        self.assertAlmostEqual(result['correction'], -0.5)

    def test_warmup_gaps_and_bad_inputs(self):
        cases = [
            ('sensor.hp_poc_parter_komfort', 'unavailable'),
            ('sensor.hp_poc_probka_outdoor', 'unknown'),
            ('sensor.hp_poc_parter_liczba_probek', 12),
            ('input_number.hp_poc_cel_parter', 'unavailable'),
        ]
        for entity, value in cases:
            with self.subTest(entity=entity):
                data = fixture()
                data[entity].state = str(value)
                harness = Harness(data)
                self.assertFalse(harness.decision()['ready'])
                self.assertFalse(harness.write_allowed())
        data = fixture()
        data['sensor.hp_poc_parter_komfort'].attributes['age_coverage_ratio'] = 0.1
        self.assertFalse(Harness(data).decision()['ready'])

    def test_write_guards(self):
        for mode in ['cooldown', 'manual_change', 'disabled_co', 'stale_source',
                     'missing_source', 'stale_decision', 'fractional', 'missing_limits', 'wrong_step']:
            with self.subTest(mode=mode):
                data = fixture()
                harness = Harness(data)
                harness.decision()
                if mode == 'cooldown': data['input_datetime.hp_poc_ostatnia_proba'].state = NOW.isoformat()
                if mode == 'manual_change': data[CO1].last_changed = NOW
                if mode == 'disabled_co': data['switch.garaz_pompa_ciepla_circuit_1_heating'].state = 'off'
                if mode == 'stale_source': data['sensor.salon_termometr_salon'].last_reported = NOW - timedelta(hours=3)
                if mode == 'missing_source': del data['sensor.salon_termometr_salon']
                if mode == 'stale_decision': data[PROPOSAL].attributes['calculated_at'] = (NOW - timedelta(hours=1)).isoformat()
                if mode == 'fractional': data[CO1].state = '28.5'
                if mode == 'missing_limits': data[CO1].attributes.pop('min')
                if mode == 'wrong_step': data[CO1].attributes['step'] = 0.5
                self.assertFalse(harness.write_allowed())

    def test_samples_reject_stale_or_implausible(self):
        entity = next(e for block in PACKAGE['template'] for e in block.get('sensor', [])
                      if e.get('name') == 'hp_poc_probka_outdoor')
        for value, age in [('40', 0), ('-50', 0), ('nan', 0), ('-5', 3600)]:
            data = fixture()
            source = data['sensor.garaz_pompa_ciepla_outdoor_ambient_temp']
            source.state, source.last_reported = value, NOW - timedelta(seconds=age)
            self.assertFalse(Harness(data).render(entity['availability'], {}))

    def test_limits_intersection(self):
        data = fixture(ground=19, upper=20, outdoor=-30)
        data[CO1].attributes['max'] = 28
        result = Harness(data).decision()
        self.assertEqual(result['rounded'], 28)
        data[CO1].attributes['min'] = 36
        self.assertFalse(Harness(data).decision()['ready'])

    def test_missing_statistics_are_not_reported_as_warmup(self):
        data = fixture()
        entity = PACKAGE['template'][0]['sensor'][0]
        harness = Harness(data)
        harness.decision()
        self.assertEqual(harness.render(entity['state'], {}), 'obliczenia_gotowe')
        del data['sensor.hp_poc_parter_liczba_probek']
        self.assertEqual(harness.render(entity['state'], {}), 'brak_encji')
        self.assertIn('sensor.hp_poc_parter_liczba_probek',
                      harness.render(entity['attributes']['missing_entities'], {}))

    def test_existing_empty_statistics_are_not_missing(self):
        data = fixture()
        data[PROPOSAL] = State(PROPOSAL, 'unavailable')
        data['sensor.hp_poc_parter_liczba_probek'].state = 'unknown'
        entity = PACKAGE['template'][0]['sensor'][0]
        harness = Harness(data)
        self.assertEqual(harness.render(entity['state'], {}), 'blokada_danych_lub_rozgrzewanie')
        self.assertEqual(harness.render(entity['attributes']['missing_entities'], {}), [])


if __name__ == '__main__':
    unittest.main()
