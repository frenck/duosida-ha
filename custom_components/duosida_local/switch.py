"""
Switch platform for Duosida Local.

Switches are on/off entities that control something on the device.
Unlike sensors which are read-only, switches can be toggled.

This integration provides two switches:
1. Charging Switch - Start/stop charging
2. Direct Mode Switch - Enable/disable plug-and-charge mode
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_ID, COORDINATOR, DOMAIN
from .coordinator import DuosidaDataUpdateCoordinator
from .entity import DuosidaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up Duosida switches.

    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration
        async_add_entities: Callback to add entities
    """
    coordinator: DuosidaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ]
    device_id = entry.data[CONF_DEVICE_ID]

    async_add_entities([
        DuosidaChargingSwitch(coordinator, device_id),
        DuosidaDirectModeSwitch(coordinator, device_id),
        DuosidaStopOnDisconnectSwitch(coordinator, device_id),
    ])


class DuosidaChargingSwitch(DuosidaEntity, SwitchEntity):
    """
    Switch to control charging.

    When turned ON: Sends start charging command
    When turned OFF: Sends stop charging command

    The switch state reflects the current charging status from the charger.
    """

    # Entity attributes
    _attr_name = "Charging"
    _attr_icon = "mdi:ev-station"

    def __init__(
        self,
        coordinator: DuosidaDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the charging switch."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_charging"

    @property
    def is_on(self) -> bool:
        """
        Return true if charging is active.

        We check the conn_status value from the charger.
        Status 2 means "Charging" is active.

        Returns:
            True if currently charging, False otherwise
        """
        if not self.coordinator.data:
            return False

        # conn_status == 2 means charging
        return self.coordinator.data.get("conn_status") == 2

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        Start charging.

        Called when user toggles the switch ON in the UI.
        Sends the start command through the coordinator.

        Args:
            **kwargs: Additional arguments (not used)
        """
        await self.coordinator.async_start_charging()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        Stop charging.

        Called when user toggles the switch OFF in the UI.

        Args:
            **kwargs: Additional arguments (not used)
        """
        await self.coordinator.async_stop_charging()


class DuosidaDirectModeSwitch(DuosidaEntity, SwitchEntity):
    """
    Switch to control direct work mode (plug and charge).

    When enabled: Charging starts automatically when a vehicle is plugged in
    When disabled: User must manually start charging

    This switch is disabled by default as it's a less common setting.
    Users can enable it in the entity settings.
    """

    _attr_name = "Direct Mode"
    _attr_icon = "mdi:lightning-bolt"
    _attr_entity_registry_enabled_default = False  # Hidden by default

    def __init__(
        self,
        coordinator: DuosidaDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the direct mode switch."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_direct_mode"

    @property
    def is_on(self) -> bool | None:
        """
        Return true if direct mode is enabled, None if unknown.

        Note: We read this from coordinator's stored settings because
        the charger doesn't report this in its status messages.

        Returns None if the user hasn't set this value yet, indicating
        the state is unknown. This prevents the integration from making
        assumptions about the charger's configuration.
        """
        return self.coordinator.get_stored_setting("direct_mode")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        Enable direct mode.

        After enabling, charging will start automatically when
        a vehicle is connected. The setting is persisted to HA storage.
        """
        if await self.coordinator.async_set_direct_mode(True):
            # Update the UI immediately
            # The coordinator already updated the stored setting
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        Disable direct mode.

        After disabling, charging must be started manually.
        The setting is persisted to HA storage.
        """
        if await self.coordinator.async_set_direct_mode(False):
            self.async_write_ha_state()


class DuosidaStopOnDisconnectSwitch(DuosidaEntity, SwitchEntity):
    """
    Switch to control stop transaction on EV disconnect.

    When enabled: Transaction stops automatically when vehicle disconnects
    When disabled: Transaction remains open after vehicle disconnects

    This is typically enabled by default for most use cases.
    """

    _attr_name = "Stop Session on Vehicle Disconnect"
    _attr_icon = "mdi:connection"
    _attr_entity_registry_enabled_default = False  # Hidden by default

    def __init__(
        self,
        coordinator: DuosidaDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the stop on disconnect switch."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_stop_on_disconnect"

    @property
    def is_on(self) -> bool | None:
        """
        Return true if stop on disconnect is enabled, None if unknown.

        Note: We read this from coordinator's stored settings because
        the charger doesn't report this in its status messages.

        Returns None if the user hasn't set this value yet, indicating
        the state is unknown. This prevents the integration from making
        assumptions about the charger's configuration.
        """
        return self.coordinator.get_stored_setting("stop_on_disconnect")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        Enable stop on disconnect.

        When enabled, the charging transaction will automatically stop
        when the vehicle is disconnected from the cable.
        """
        if await self.coordinator.async_set_stop_on_disconnect(True):
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        Disable stop on disconnect.

        When disabled, the transaction remains open even after
        the vehicle disconnects.
        """
        if await self.coordinator.async_set_stop_on_disconnect(False):
            self.async_write_ha_state()
