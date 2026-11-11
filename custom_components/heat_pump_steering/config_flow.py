"""ConfigEntry version registration for the I01 foundation.

The manifest does not advertise a user config flow. I02 will add the complete
creator; this class only lets Home Assistant validate/migrate existing entries.
"""

from homeassistant import config_entries

from .const import CONFIG_ENTRY_VERSION, DOMAIN


class HeatPumpSteeringConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Register the current entry version without creating incomplete entries."""

    VERSION = CONFIG_ENTRY_VERSION
    MINOR_VERSION = 1
