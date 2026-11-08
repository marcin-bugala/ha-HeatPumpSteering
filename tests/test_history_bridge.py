"""Exercise the actual package import and Recorder adapter with HA stand-ins."""
import importlib.util
import sys
from datetime import datetime, timezone
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from test_poc import ROOT


class HistoryBridgeTests(unittest.TestCase):
    def test_local_history_submodule_does_not_shadow_recorder_api(self):
        modules = {}

        def module(name, **attrs):
            value = ModuleType(name)
            value.__dict__.update(attrs)
            modules[name] = value
            return value

        module('voluptuous', Optional=lambda key, **kwargs: key,
               Schema=lambda *args, **kwargs: None, ALLOW_EXTRA=object())
        module('sqlalchemy', select=MagicMock())
        api = SimpleNamespace(get_significant_states=MagicMock(return_value={}))
        module('homeassistant.components.recorder', get_instance=MagicMock(), history=api)
        class Field:
            def __le__(self, other): return True
            def __ge__(self, other): return True
            def is_(self, other): return True
        module('homeassistant.components.recorder.db_schema',
               RecorderRuns=SimpleNamespace(start=Field(), end=Field()))
        module('homeassistant.helpers', config_validation=SimpleNamespace(entity_id=str))
        session_scope = MagicMock()
        session_scope.return_value.__enter__.return_value.scalars.return_value.all.return_value = []
        module('homeassistant.helpers.recorder', session_scope=session_scope)
        module('homeassistant.helpers.start', async_at_started=MagicMock())
        module('homeassistant.util', dt=SimpleNamespace(as_utc=lambda date: date))

        name = 'hp_poc_history_bridge_test'
        spec = importlib.util.spec_from_file_location(name,
            ROOT / 'custom_components/hp_poc_history/__init__.py',
            submodule_search_locations=[str(ROOT / 'custom_components/hp_poc_history')])
        package = importlib.util.module_from_spec(spec)
        modules[name] = package
        with patch.dict(sys.modules, modules):
            try:
                spec.loader.exec_module(package)
                # Python binds the relative history submodule onto the package.
                self.assertIsInstance(package.history, ModuleType)
                now = datetime.now(timezone.utc)
                hass = object()
                events, runs = package._read(hass, now, now, ['sensor.example'])
                api.get_significant_states.assert_called_once_with(
                    hass, now, now, entity_ids=['sensor.example'],
                    include_start_time_state=True, significant_changes_only=False,
                    minimal_response=False, no_attributes=True)
                self.assertEqual(events, [[]])
                self.assertEqual(runs, [])
            finally:
                sys.modules.pop(name + '.history', None)


if __name__ == '__main__':
    unittest.main()
