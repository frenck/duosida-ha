"""Test Duosida EV coordinator."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.duosida_ev.coordinator import DuosidaDataUpdateCoordinator


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_charger: Any) -> DuosidaDataUpdateCoordinator:
    """Return a coordinator instance."""
    return DuosidaDataUpdateCoordinator(
        hass,
        mock_charger,
        scan_interval=10,
        device_id="03123456789012345678",
    )


async def test_coordinator_update_success(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator successfully updates data."""
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert coordinator.data["conn_status"] == 2  # Charging
    assert coordinator.data["voltage"] == 230.0
    assert coordinator.data["current"] == 16.0
    assert coordinator.data["power"] == 11040


async def test_coordinator_update_connection_error(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator handles connection errors."""
    # Make the charger raise an error
    coordinator.charger.connect = MagicMock(return_value=False)

    with pytest.raises(UpdateFailed):
        await coordinator.async_config_entry_first_refresh()


async def test_coordinator_set_max_current(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set max current."""
    # First refresh to get initial data
    await coordinator.async_config_entry_first_refresh()

    # Set max current
    result = await coordinator.async_set_max_current(20)
    assert result is True

    # Verify the setting was persisted
    assert coordinator.get_stored_setting("max_current") == 20


async def test_coordinator_set_led_brightness(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set LED brightness."""
    await coordinator.async_config_entry_first_refresh()

    # Set LED brightness (valid values: 0, 1, 3)
    result = await coordinator.async_set_led_brightness(3)
    assert result is True

    assert coordinator.get_stored_setting("led_brightness") == 3


async def test_coordinator_set_direct_mode(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set direct mode."""
    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_set_direct_mode(True)
    assert result is True

    assert coordinator.get_stored_setting("direct_mode") is True


async def test_coordinator_start_charging(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can start charging."""
    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_start_charging()
    assert result is True


async def test_coordinator_stop_charging(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can stop charging."""
    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_stop_charging()
    assert result is True


async def test_coordinator_energy_integration(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator integrates power to calculate total energy."""
    await coordinator.async_config_entry_first_refresh()

    # Get initial data

    # Simulate time passing and another update with power consumption
    with patch("homeassistant.core.HomeAssistant.loop") as mock_loop:
        # First update at time 0
        mock_loop.time.return_value = 0.0
        await coordinator._async_update_data()
        energy_after_first = coordinator.data["total_energy"]

        # Second update 1 hour later with 11040W power
        mock_loop.time.return_value = 3600.0  # 1 hour = 3600 seconds
        coordinator.charger._status["power"] = 11040  # 11.04 kW
        await coordinator._async_update_data()
        energy_after_second = coordinator.data["total_energy"]

        # Energy should have increased
        # 11.04 kW * 1 hour = 11.04 kWh (approximately)
        assert energy_after_second > energy_after_first


async def test_coordinator_reset_total_energy(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can reset total energy."""
    await coordinator.async_config_entry_first_refresh()

    # Set some energy value
    coordinator._stored_settings["total_energy"] = 100.0

    # Reset
    await coordinator.async_reset_total_energy()

    assert coordinator.get_stored_setting("total_energy") == 0.0


async def test_coordinator_settings_persistence(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator persists settings to storage."""
    await coordinator.async_load_stored_settings()
    await coordinator.async_config_entry_first_refresh()

    # Set multiple settings
    await coordinator.async_set_led_brightness(3)
    await coordinator.async_set_direct_mode(True)
    await coordinator.async_set_max_current(20)

    # Settings should be persisted
    assert coordinator.get_stored_setting("led_brightness") == 3
    assert coordinator.get_stored_setting("direct_mode") is True
    assert coordinator.get_stored_setting("max_current") == 20


async def test_coordinator_unknown_first_approach(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator doesn't set defaults, keeps settings as unknown."""
    await coordinator.async_load_stored_settings()

    # Before any user interaction, settings should be None (unknown)
    assert coordinator.get_stored_setting("led_brightness") is None
    assert coordinator.get_stored_setting("direct_mode") is None
    assert coordinator.get_stored_setting("max_voltage") is None
    assert coordinator.get_stored_setting("min_voltage") is None


async def test_coordinator_set_max_voltage(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set max voltage."""
    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_set_max_voltage(280)
    assert result is True

    assert coordinator.get_stored_setting("max_voltage") == 280


async def test_coordinator_set_min_voltage(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set min voltage."""
    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_set_min_voltage(90)
    assert result is True

    assert coordinator.get_stored_setting("min_voltage") == 90


async def test_coordinator_disconnect(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator disconnects from charger."""
    await coordinator.async_config_entry_first_refresh()

    # Charger should be connected after refresh
    assert coordinator.charger._connected is True

    # Disconnect
    coordinator.disconnect()

    # Charger should be disconnected
    assert coordinator.charger._connected is False
