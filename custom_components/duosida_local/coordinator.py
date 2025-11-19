"""
Data update coordinator for Duosida Local.

The coordinator is a central piece of Home Assistant integrations. It:
1. Fetches data from the device at regular intervals
2. Stores the latest data
3. Notifies all entities when new data arrives
4. Handles connection errors and retries
5. Persists configuration settings that the charger doesn't report back

This pattern ensures:
- Only one connection to the device (not one per entity)
- All entities update simultaneously
- Proper error handling in one place
- Settings are synchronized between HA and charger

How it works:
1. On startup, load persisted settings from HA storage
2. Connect to charger and sync settings
3. Home Assistant calls _async_update_data() every scan_interval seconds
4. We fetch status from the charger
5. All entities automatically get notified and update their state
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from duosida_ev import DuosidaCharger

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Storage version - increment if storage format changes
STORAGE_VERSION = 1


class DuosidaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """
    Class to manage fetching Duosida data.

    Inherits from DataUpdateCoordinator which provides:
    - Automatic polling at specified interval
    - Error handling and retry logic
    - Listener management for entities

    The generic type [dict[str, Any]] indicates this coordinator
    stores data as a dictionary (the charger status).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        charger: DuosidaCharger,
        scan_interval: int,
        device_id: str,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            charger: The DuosidaCharger instance for communication
            scan_interval: How often to fetch data (in seconds)
            device_id: Device ID for storage key
        """
        # Initialize the parent class
        # This sets up the polling mechanism
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,  # Used in log messages
            update_interval=timedelta(seconds=scan_interval),
        )

        # Store the charger instance for later use
        self.charger = charger

        # Track if we've done initial settings sync
        # Connection is now opened/closed for each operation

        # Device ID for storage
        self._device_id = device_id

        # Storage for persisting settings that charger doesn't report back
        # Key format: duosida_local.{device_id}
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.{device_id}",
        )

        # Current stored settings (loaded from storage)
        # These are settings the charger doesn't report back
        # Initially None because we don't know the charger's actual configuration
        # Values are only stored when the user explicitly changes them in HA
        self._stored_settings: dict[str, Any] = {
            "led_brightness": None,        # Unknown until user sets it
            "direct_mode": None,           # Unknown until user sets it
            "stop_on_disconnect": None,    # Unknown until user sets it
            "max_voltage": None,           # Unknown until user sets it
            "min_voltage": None,           # Unknown until user sets it
            "total_energy": 0.0,           # Total energy consumed (kWh) - integrated from power
            "last_power": 0.0,             # Last power reading (W) for integration
            "last_update_time": None,      # Last update timestamp for integration
        }

        # Flag to track if we've synced user settings on first connection after HA restart
        # This prevents re-syncing on every poll (every 10 seconds)
        # Only user-set values (non-None) are synced
        self._settings_synced_this_session = False

    async def async_load_stored_settings(self) -> None:
        """
        Load stored settings from Home Assistant storage.

        This should be called during setup, before the first refresh.
        Settings are stored in .storage/duosida_local.{device_id}
        """
        stored = await self._store.async_load()

        if stored:
            _LOGGER.debug("Loaded stored settings: %s", stored)
            # Merge with defaults (in case new settings were added)
            self._stored_settings.update(stored)
        else:
            _LOGGER.debug("No stored settings found, using defaults")

    async def _async_save_stored_settings(self) -> None:
        """
        Save current settings to Home Assistant storage.

        Called whenever a setting is changed to persist it.
        """
        await self._store.async_save(self._stored_settings)
        _LOGGER.debug("Saved settings to storage: %s", self._stored_settings)

    async def _async_sync_settings_to_charger(self) -> None:
        """
        Sync stored settings to the charger.

        Called on first successful connection to restore settings that
        the user has explicitly configured in Home Assistant.

        IMPORTANT: Only syncs values that are not None (i.e., values the user
        has explicitly set). We don't sync default values because we don't
        know what the charger's actual configuration is.
        """
        settings_to_sync = []

        # Sync LED brightness (only if user has set it)
        led_brightness = self._stored_settings.get("led_brightness")
        if led_brightness is not None:
            settings_to_sync.append(f"LED brightness: {led_brightness}")
            await self.hass.async_add_executor_job(
                self.charger.set_led_brightness, led_brightness
            )

        # Sync direct work mode (only if user has set it)
        direct_mode = self._stored_settings.get("direct_mode")
        if direct_mode is not None:
            settings_to_sync.append(f"direct mode: {direct_mode}")
            await self.hass.async_add_executor_job(
                self.charger.set_direct_work_mode, direct_mode
            )

        # Sync stop on disconnect (only if user has set it)
        stop_on_disconnect = self._stored_settings.get("stop_on_disconnect")
        if stop_on_disconnect is not None:
            settings_to_sync.append(f"stop on disconnect: {stop_on_disconnect}")
            await self.hass.async_add_executor_job(
                self.charger.set_stop_on_disconnect, stop_on_disconnect
            )

        # Sync max voltage (only if user has set it)
        max_voltage = self._stored_settings.get("max_voltage")
        if max_voltage is not None:
            settings_to_sync.append(f"max voltage: {max_voltage}V")
            await self.hass.async_add_executor_job(
                self.charger.set_max_voltage, max_voltage
            )

        # Sync min voltage (only if user has set it)
        min_voltage = self._stored_settings.get("min_voltage")
        if min_voltage is not None:
            settings_to_sync.append(f"min voltage: {min_voltage}V")
            await self.hass.async_add_executor_job(
                self.charger.set_min_voltage, min_voltage
            )

        if settings_to_sync:
            _LOGGER.info("Synced user-configured settings to charger: %s", ", ".join(settings_to_sync))
        else:
            _LOGGER.info("No user-configured settings to sync (charger retains its current configuration)")

    def get_stored_setting(self, key: str) -> Any:
        """
        Get a stored setting value.

        Args:
            key: Setting key (e.g., "led_brightness", "direct_mode")

        Returns:
            The stored value, or None if not found
        """
        return self._stored_settings.get(key)

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Fetch data from the charger.

        This method is called automatically by the parent class
        at the interval specified in update_interval.

        Opens a connection, gets status, and closes connection each time.
        This is more reliable for chargers with limited connection handling.

        Returns:
            Dictionary containing charger status data

        Raises:
            UpdateFailed: If we can't get data from the charger
                         (causes HA to show entity as unavailable)
        """
        try:
            # Connect to charger
            _LOGGER.debug("Connecting to charger at %s", self.charger.host)

            connected = await self.hass.async_add_executor_job(
                self.charger.connect
            )

            if not connected:
                raise UpdateFailed("Failed to connect to charger")

            try:
                # Small delay after connect - charger needs time to be ready
                import asyncio
                await asyncio.sleep(0.3)
                _LOGGER.debug("Connection ready, starting data fetch")

                # Sync user-configured settings on first successful connection after HA restart
                # Only syncs values that the user has explicitly set (non-None values)
                if not self._settings_synced_this_session:
                    await self._async_sync_settings_to_charger()
                    self._settings_synced_this_session = True

                # Get the current status from the charger
                _LOGGER.debug("Requesting status from charger")
                status = await self.hass.async_add_executor_job(self.charger.get_status)

                if not status:
                    _LOGGER.warning("Charger returned no status")
                    raise UpdateFailed("Failed to get status from charger")

                # Convert the ChargerStatus object to a dictionary
                data = status.to_dict()
                _LOGGER.debug(
                    "Got status: state=%s, voltage=%.1fV, current=%.2fA, power=%.0fW",
                    data.get("state"),
                    data.get("voltage", 0),
                    data.get("current", 0),
                    data.get("power", 0)
                )

                # Add max_current from cached value (not part of telemetry)
                max_current = self.charger.get_max_current()
                if max_current is not None:
                    data["max_current"] = max_current

                # Integrate power over time to calculate total energy
                # This creates an always-increasing energy meter for HA Energy Dashboard
                current_power = data.get("power", 0.0) or 0.0
                current_time = self.hass.loop.time()

                # Get stored values
                last_power = self._stored_settings.get("last_power", 0.0) or 0.0
                last_time = self._stored_settings.get("last_update_time")
                total_energy = self._stored_settings.get("total_energy", 0.0) or 0.0

                # Calculate energy delta using trapezoidal integration
                # Energy (kWh) = Average Power (W) * Time (hours)
                if last_time is not None and current_time > last_time:
                    time_delta_hours = (current_time - last_time) / 3600.0
                    average_power = (current_power + last_power) / 2.0
                    energy_delta = (average_power * time_delta_hours) / 1000.0  # Convert W to kW

                    # Only add positive energy (ignore negative spikes from bad readings)
                    if energy_delta > 0 and energy_delta < 100:  # Sanity check: < 100 kWh per interval
                        total_energy += energy_delta
                        _LOGGER.debug(
                            "Energy integration: %.3f kWh (avg power: %.1f W, time: %.3f h)",
                            energy_delta, average_power, time_delta_hours
                        )

                # Update stored state
                self._stored_settings["total_energy"] = total_energy
                self._stored_settings["last_power"] = current_power
                self._stored_settings["last_update_time"] = current_time

                # Save to storage (async, fire and forget to avoid blocking)
                self.hass.async_create_task(self._async_save_stored_settings())

                # Add total_energy to data
                data["total_energy"] = total_energy

                return data

            finally:
                # Always disconnect after getting status
                await self.hass.async_add_executor_job(self.charger.disconnect)
                _LOGGER.debug("Disconnected from charger")

        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Error communicating with charger: %s", err)
            raise UpdateFailed(f"Error communicating with charger: {err}") from err

    async def _async_send_command(self, command_func, command_name: str) -> bool:
        """
        Send a command to the charger with connect/disconnect.

        Args:
            command_func: The charger method to call
            command_name: Name for logging

        Returns:
            True if command was sent successfully
        """
        try:
            _LOGGER.info("Sending %s command", command_name)

            # Connect
            connected = await self.hass.async_add_executor_job(self.charger.connect)
            if not connected:
                _LOGGER.error("Failed to connect for %s", command_name)
                return False

            try:
                # Small delay after connect - charger needs time to be ready
                import asyncio
                await asyncio.sleep(0.3)

                # Send command
                result = await self.hass.async_add_executor_job(command_func)
                return result
            finally:
                # Always disconnect
                await self.hass.async_add_executor_job(self.charger.disconnect)

        except Exception as err:
            _LOGGER.error("Error in %s: %s", command_name, err)
            return False

    async def async_start_charging(self) -> bool:
        """
        Start charging the vehicle.

        Returns:
            True if command was sent successfully
        """
        result = await self._async_send_command(
            self.charger.start_charging, "start charging"
        )

        if result:
            # Wait for charger to update state, then refresh
            import asyncio
            await asyncio.sleep(1.0)
            await self.async_request_refresh()

        return result

    async def async_stop_charging(self) -> bool:
        """
        Stop charging the vehicle.

        Returns:
            True if command was sent successfully
        """
        result = await self._async_send_command(
            self.charger.stop_charging, "stop charging"
        )

        if result:
            # Wait for charger to update state, then refresh
            import asyncio
            await asyncio.sleep(1.0)
            await self.async_request_refresh()

        return result

    async def async_set_max_current(self, current: int) -> bool:
        """
        Set the maximum charging current.

        Args:
            current: Current in amperes (6-32)

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        result = await self._async_send_command(
            partial(self.charger.set_max_current, current),
            f"set max current to {current}A"
        )

        if result:
            import asyncio
            await asyncio.sleep(0.5)
            await self.async_request_refresh()

        return result

    async def async_set_led_brightness(self, level: int) -> bool:
        """
        Set LED/screen brightness level.

        Args:
            level: Brightness (0=off, 1=low, 3=high)

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        result = await self._async_send_command(
            partial(self.charger.set_led_brightness, level),
            f"set LED brightness to {level}"
        )

        if result:
            # Persist the setting
            self._stored_settings["led_brightness"] = level
            await self._async_save_stored_settings()

        return result

    async def async_set_direct_mode(self, enabled: bool) -> bool:
        """
        Set direct work mode (plug and charge).

        When enabled, charging starts automatically when a vehicle is connected.
        When disabled, charging must be started manually.

        Args:
            enabled: True to enable, False to disable

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        state = "enabled" if enabled else "disabled"
        result = await self._async_send_command(
            partial(self.charger.set_direct_work_mode, enabled),
            f"set direct mode to {state}"
        )

        if result:
            # Persist the setting
            self._stored_settings["direct_mode"] = enabled
            await self._async_save_stored_settings()

        return result

    async def async_set_stop_on_disconnect(self, enabled: bool) -> bool:
        """
        Set whether to stop transaction when EV side disconnects.

        When enabled, charging transaction stops automatically when
        the vehicle disconnects from the cable.

        Args:
            enabled: True to enable auto-stop, False to disable

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        state = "enabled" if enabled else "disabled"
        result = await self._async_send_command(
            partial(self.charger.set_stop_on_disconnect, enabled),
            f"set stop on disconnect to {state}"
        )

        if result:
            # Persist the setting
            self._stored_settings["stop_on_disconnect"] = enabled
            await self._async_save_stored_settings()

        return result

    async def async_set_max_voltage(self, voltage: int) -> bool:
        """
        Set maximum working voltage.

        If grid voltage exceeds this value, charging will stop.

        Args:
            voltage: Maximum voltage in volts (265-290V)

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        result = await self._async_send_command(
            partial(self.charger.set_max_voltage, voltage),
            f"set max voltage to {voltage}V"
        )

        if result:
            # Persist the setting
            self._stored_settings["max_voltage"] = voltage
            await self._async_save_stored_settings()

        return result

    async def async_set_min_voltage(self, voltage: int) -> bool:
        """
        Set minimum working voltage.

        If grid voltage falls below this value, charging will stop.

        Args:
            voltage: Minimum voltage in volts (70-110V)

        Returns:
            True if command was sent successfully
        """
        from functools import partial
        result = await self._async_send_command(
            partial(self.charger.set_min_voltage, voltage),
            f"set min voltage to {voltage}V"
        )

        if result:
            # Persist the setting
            self._stored_settings["min_voltage"] = voltage
            await self._async_save_stored_settings()

        return result

    async def async_reset_total_energy(self) -> None:
        """
        Reset the total energy counter to zero.

        This is useful when you want to start tracking from a new baseline,
        for example at the beginning of a billing period or after a move.
        """
        _LOGGER.info("Resetting total energy counter")
        self._stored_settings["total_energy"] = 0.0
        self._stored_settings["last_power"] = 0.0
        self._stored_settings["last_update_time"] = None
        await self._async_save_stored_settings()
        await self.async_request_refresh()

    def disconnect(self) -> None:
        """
        Disconnect from the charger.

        Called when the integration is unloaded to clean up resources.
        With the new connect/disconnect pattern, this is a no-op since
        connections are closed after each operation.
        """
        # No persistent connection to close
        pass
