"""Build reviewable HA API configs; does not connect to or change HA."""
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'templates/shadow_observation.jinja').read_text(encoding='utf-8')
CALL = r"""
{% set p=state_attr('sensor.hp_poc_pamiec','payload') or {} %}
{% set old=states('input_text.hp_poc_porownanie_pamiec') | from_json({}) %}
{% set ns=namespace(fresh=true) %}
{% if not is_state('input_boolean.hp_poc_cele_zainicjalizowane','on')
      or not is_number(states('input_number.hp_poc_cel_parter'))
      or not is_number(states('input_number.hp_poc_cel_pietro')) %}{% set ns.fresh=false %}{% endif %}
{% for entity in ['sensor.salon_termometr_salon','sensor.korytarz_termometr_pietro'] %}
  {% set s=states[entity] %}
  {% if s is not defined or not is_number(s.state) or not (10 <= s.state|float(0) <= 35)
        or not (0 <= as_timestamp(now())-as_timestamp(s.last_reported,0) < 7200) %}
    {% set ns.fresh=false %}
  {% endif %}
{% endfor %}
{% set valid=is_number(states('sensor.hp_poc_co1_propozycja'))
    and is_number(state_attr('number.garaz_pompa_ciepla_circuit_1_setpoint','min'))
    and is_number(state_attr('number.garaz_pompa_ciepla_circuit_1_setpoint','max'))
    and 0 <= as_timestamp(now())-as_timestamp(state_attr('sensor.hp_poc_co1_propozycja','calculated_at'),0) < 600 %}
{% set compute=observe | as_function %}
{{ compute(p,old,as_timestamp(now())|int,
    states('input_number.hp_poc_cel_parter')|float(21),states('input_number.hp_poc_cel_pietro')|float(22),
    states('sensor.salon_termometr_salon')|float(0),states('sensor.korytarz_termometr_pietro')|float(0),
    ns.fresh,valid,is_state('input_boolean.hp_poc_auto_stop_co1','on'),
    states('switch.garaz_pompa_ciepla_circuit_1_heating'),
    as_timestamp(states('input_datetime.hp_poc_ostatnia_proba_co1_on_off'),0)) }}
"""


def build():
    automation = {
        'alias': 'Ogrzewanie POC · porównanie filtrów bez sterowania',
        'description': 'Obserwacja median 2 h/3 h, szybkiego filtra 45 min i trendu 2 h. Zapisuje wyłącznie dane porównania; nie wysyła poleceń urządzeniom.',
        'mode': 'single',
        'triggers': [
            {'trigger': 'time_pattern', 'minutes': '/1', 'seconds': '20'},
            {'trigger': 'homeassistant', 'event': 'start'},
        ],
        'actions': [
            {'variables': {'observation': SOURCE + CALL}},
            {'action': 'input_text.set_value', 'target': {'entity_id': 'input_text.hp_poc_porownanie_pamiec'},
             'data': {'value': '{{ observation.clock | to_json }}'}},
            {'action': 'input_text.set_value', 'target': {'entity_id': 'input_text.hp_poc_porownanie_dane'},
             'data': {'value': '{{ observation.data | to_json }}'}},
        ],
    }
    helpers = []
    for suffix, key, unit in [
        ('parter_2h','g2','°C'),('pietro_2h','u2','°C'),
        ('parter_45min','gf','°C'),('pietro_45min','uf','°C'),
        ('parter_trend_2h','dg','°C/h'),('pietro_trend_2h','du','°C/h'),
        ('co1_2h','c2','°C'),('co1_3h','c3','°C'),
    ]:
        prefix = "{% set d=states('input_text.hp_poc_porownanie_dane')|from_json({}) %}"
        fresh = "0 <= as_timestamp(now())-d.get('t',0) < 600"
        config = {'next_step_id': 'sensor',
                  'state': prefix + "{{ d.get('"+key+"') if "+fresh+" else none }}",
                  'availability': prefix + "{{ "+fresh+" and is_number(d.get('"+key+"')) }}",
                  'unit_of_measurement': unit}
        if unit == '°C': config['device_class'] = 'temperature'
        helpers.append({'helper_type': 'template', 'name': 'hp_poc_porownanie_'+suffix, 'config': config})
    helpers.append({'helper_type': 'template', 'name': 'hp_poc_porownanie_decyzja', 'config': {
        'next_step_id': 'sensor',
        'state': "{% set d=states('input_text.hp_poc_porownanie_dane')|from_json({}) %}{{ d.get('q','data') if 0 <= as_timestamp(now())-d.get('t',0) < 600 else 'data' }}"}})
    storage = [{'helper_type':'input_text','name':name,'config':{'max':255,'mode':'text'}}
               for name in ['hp_poc_porownanie_dane','hp_poc_porownanie_pamiec']]
    return {'storage_helpers': storage, 'automation': automation, 'helpers': helpers}


if __name__ == '__main__':
    config = build()
    folder = ROOT / 'deploy'
    folder.mkdir(exist_ok=True)
    (folder / 'shadow_api.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (folder / 'shadow_automation.yaml').write_text(yaml.safe_dump(config['automation'], allow_unicode=True, sort_keys=False), encoding='utf-8')
    print('Generated deploy/shadow_api.json and deploy/shadow_automation.yaml')
