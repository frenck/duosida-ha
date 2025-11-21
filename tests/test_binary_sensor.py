"""Test Duosida EV binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant


async def test_charging_binary_sensor(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test charging binary sensor."""
    # Check charging binary sensor exists
    charging_sensor = hass.states.get(
        "binary_sensor.duosida_ev_charger_192_168_1_100_charging"
    )
    assert charging_sensor is not None

    # conn_status 2 = charging, so sensor should be ON
    assert charging_sensor.state == "on"


async def test_charging_binary_sensor_off(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test charging binary sensor when not charging."""
    from custom_components.duosida_ev.binary_sensor import DuosidaChargingBinarySensor
    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a binary sensor instance directly
    sensor = DuosidaChargingBinarySensor(coordinator, "03123456789012345678")

    # Test is_on when conn_status is not 2
    coordinator.data = {"conn_status": 0}  # Available
    assert sensor.is_on is False

    coordinator.data = {"conn_status": 1}  # Preparing
    assert sensor.is_on is False

    coordinator.data = {"conn_status": 5}  # Finished
    assert sensor.is_on is False


async def test_charging_binary_sensor_no_data(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test charging binary sensor when coordinator has no data."""
    from custom_components.duosida_ev.binary_sensor import DuosidaChargingBinarySensor
    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a binary sensor instance directly
    sensor = DuosidaChargingBinarySensor(coordinator, "03123456789012345678")

    # Test is_on when coordinator.data is None
    coordinator.data = None
    assert sensor.is_on is False
