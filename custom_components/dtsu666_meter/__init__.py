"""DTSU666 Energy Meter (Modbus TCP) integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SLAVE_ID, DEFAULT_SCAN_INTERVAL
from .coordinator import Dtsu666Coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type Dtsu666ConfigEntry = ConfigEntry[Dtsu666Coordinator]


def _scan_interval(entry: Dtsu666ConfigEntry) -> float:
    """Options override data; fall back to the default. May be sub-second."""
    return float(
        entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: Dtsu666ConfigEntry
) -> bool:
    """Set up DTSU666 from a config entry."""
    coordinator = Dtsu666Coordinator(
        hass,
        entry,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        slave_id=entry.data[CONF_SLAVE_ID],
        scan_interval=_scan_interval(entry),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: Dtsu666ConfigEntry
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded


async def _async_reload_entry(
    hass: HomeAssistant, entry: Dtsu666ConfigEntry
) -> None:
    """Reload when the user changes options (e.g. scan interval)."""
    await hass.config_entries.async_reload(entry.entry_id)
