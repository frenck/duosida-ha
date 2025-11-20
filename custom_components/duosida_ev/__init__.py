"""
The Duosida Local integration for Home Assistant.

This is the main entry point for the integration. Home Assistant calls these
functions when the integration is set up or removed.

Key concepts:
- ConfigEntry: Stores the user's configuration (IP, device ID, etc.)
- Platform: A type of entity (sensor, switch, button, etc.)
- Coordinator: Manages data fetching and updates all entities
"""

from __future__ import annotations

import logging

from duosida_ev import DuosidaCharger  # type: ignore[attr-defined]
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import DuosidaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Define which platforms (entity types) this integration provides
# Each platform has its own file (sensor.py, switch.py, etc.)
PLATFORMS: list[Platform] = [
    Platform.SENSOR,  # Read-only values (voltage, current, etc.)
    Platform.SWITCH,  # On/off controls (charging, direct mode)
    Platform.NUMBER,  # Numeric controls (max current, LED brightness)
    Platform.BUTTON,  # Action triggers (start/stop buttons)
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Duosida Local from a config entry.

    This function is called by Home Assistant when:
    1. User adds the integration through the UI
    2. Home Assistant starts and loads saved integrations

    Args:
        hass: The Home Assistant instance
        entry: The configuration entry containing user settings

    Returns:
        True if setup was successful, False otherwise
    """
    # Initialize storage for this integration's data
    # hass.data is a dictionary shared across Home Assistant
    # We use DOMAIN as key to avoid conflicts with other integrations
    hass.data.setdefault(DOMAIN, {})

    # Extract configuration from the entry
    # These values were saved during the config flow
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 9988)
    device_id = entry.data[CONF_DEVICE_ID]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.debug(
        "Setting up Duosida charger at %s:%s (device_id: %s)", host, port, device_id
    )

    # Create the charger instance from our library
    # This handles all the low-level TCP communication
    charger = DuosidaCharger(
        host=host,
        port=port,
        device_id=device_id,
        debug=False,  # Set to True for protocol-level debugging
    )

    # Create the coordinator
    # The coordinator is responsible for:
    # - Fetching data from the charger periodically
    # - Notifying all entities when new data is available
    # - Handling errors and retries
    # - Persisting and syncing settings the charger doesn't report back
    coordinator = DuosidaDataUpdateCoordinator(
        hass,
        charger,
        scan_interval,
        device_id,  # Pass device_id for storage key
    )

    # Load stored settings (LED brightness, direct mode) before first refresh
    # These are settings the charger doesn't report back
    await coordinator.async_load_stored_settings()

    # Fetch initial data before setting up entities
    # This ensures entities have data when they're created
    # If this fails, the setup will fail and HA will retry later
    # Note: This also syncs stored settings to charger on first connection
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator so other parts of the integration can access it
    # Each config entry has its own entry_id (unique identifier)
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    # Set up all platforms (sensors, switches, etc.)
    # This calls async_setup_entry() in each platform file
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Duosida charger at %s set up successfully", host)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.

    This function is called when:
    1. User removes the integration
    2. User disables the integration
    3. Home Assistant is shutting down

    Args:
        hass: The Home Assistant instance
        entry: The configuration entry being unloaded

    Returns:
        True if unload was successful, False otherwise
    """
    # Unload all platforms
    # This removes all entities created by this config entry
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Disconnect from the charger to free up resources
        coordinator: DuosidaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
            COORDINATOR
        ]
        coordinator.disconnect()

        # Remove our data from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Duosida charger unloaded successfully")

    return unload_ok
