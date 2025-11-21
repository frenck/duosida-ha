"""
Binary sensor platform for Duosida EV Charger.

Binary sensors are read-only on/off entities that indicate a state.
Unlike switches, they cannot be controlled - they only report status.

This integration provides:
1. Charging binary sensor - Shows if the charger is currently charging
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    Set up Duosida binary sensors.

    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration
        async_add_entities: Callback to add entities
    """
    coordinator: DuosidaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ]
    device_id = entry.data[CONF_DEVICE_ID]

    async_add_entities(
        [
            DuosidaChargingBinarySensor(coordinator, device_id),
        ]
    )


class DuosidaChargingBinarySensor(DuosidaEntity, BinarySensorEntity):
    """
    Binary sensor indicating charging status.

    This is a read-only sensor that shows whether the charger is
    currently actively charging a vehicle.

    Use the Start/Stop Charging buttons to control charging.
    """

    _attr_name = "Charging"
    _attr_icon = "mdi:ev-station"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(
        self,
        coordinator: DuosidaDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the charging binary sensor."""
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
