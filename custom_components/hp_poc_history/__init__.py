"""Populate YAML POC memory from Recorder. Never send device commands."""
import asyncio
from datetime import timedelta
from functools import partial
import logging

import voluptuous as vol
from sqlalchemy import select

from homeassistant.components.recorder import get_instance, history
from homeassistant.components.recorder.db_schema import RecorderRuns
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.recorder import session_scope
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from .history import LOOKBACK, reconstruct

DOMAIN = 'hp_poc_history'
EVENT = 'hp_poc_history_loaded'
DEFAULTS = {
    'ground': 'sensor.salon_termometr_salon',
    'upper': 'sensor.korytarz_termometr_pietro',
    'outdoor': 'sensor.garaz_pompa_ciepla_outdoor_ambient_temp',
    'co1': 'switch.garaz_pompa_ciepla_circuit_1_heating',
    'setpoint': 'number.garaz_pompa_ciepla_circuit_1_setpoint',
}
CONFIG_SCHEMA = vol.Schema({vol.Optional(DOMAIN): vol.Schema({
    vol.Optional(key, default=value): cv.entity_id for key, value in DEFAULTS.items()
})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)


def _read(hass, start, end, entities):
    """Use Recorder's executor/session; no direct database file or SQL writes."""
    states = history.get_significant_states(
        hass, start, end, entity_ids=entities, include_start_time_state=True,
        significant_changes_only=False, minimal_response=False, no_attributes=True,
    )
    events = [[(s.last_updated.timestamp(), s.state) for s in states.get(entity, [])]
              for entity in entities]
    with session_scope(hass=hass, read_only=True) as session:
        runs = [(dt_util.as_utc(run.start).timestamp(),
                 dt_util.as_utc(run.end).timestamp() if run.end else end.timestamp())
                for run in session.scalars(select(RecorderRuns).where(
                    RecorderRuns.start <= end,
                    (RecorderRuns.end.is_(None)) | (RecorderRuns.end >= start),
                )).all()]
    return events, runs


async def async_setup(hass, config):
    """Register a refresh action and perform one startup reconstruction."""
    options = config[DOMAIN]
    entities = [options[key] for key in DEFAULTS]
    lock = asyncio.Lock()

    async def refresh(_call=None):
        async with lock:
            recorder = get_instance(hass)
            if not await asyncio.shield(recorder.async_db_ready):
                raise RuntimeError('Recorder database is not ready')
            if not recorder.enabled:
                raise RuntimeError('Recorder is disabled')
            now = dt_util.utcnow()
            current = [hass.states.get(entity) for entity in entities]
            if any(state is None for state in current):
                raise RuntimeError('POC source entities are not loaded yet')
            for state in current[:3]:
                if state.attributes.get('unit_of_measurement') != '°C':
                    raise ValueError(f'Expected °C for {state.entity_id}')
            events, runs = await recorder.async_add_executor_job(partial(
                _read, hass, now - timedelta(seconds=LOOKBACK + 300), now, entities))
            seed = await hass.async_add_executor_job(
                reconstruct, events, runs, now.timestamp(),
                [current[3].state, current[4].state])
            seed['entities'] = entities
            hass.bus.async_fire(EVENT, seed)
            _LOGGER.info('History sent to POC memory: %s raw slots, %s trend slots',
                         len(seed['raw']), len(seed['trend']))

    async def startup(_hass):
        for attempt in range(3):
            try:
                await refresh()
                return
            except Exception:  # Startup failure leaves normal live sampling active.
                _LOGGER.exception('Cannot seed POC history (attempt %s/3)', attempt + 1)
                if attempt < 2:
                    await asyncio.sleep(60)

    hass.services.async_register(DOMAIN, 'refresh', refresh, schema=vol.Schema({}))
    async_at_started(hass, startup)
    return True
