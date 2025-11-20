"""Test Duosida EV coordinator."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.coordinator import DuosidaDataUpdateCoordinator


@pytest.fixture
async def coordinator(
    hass: HomeAssistant, mock_charger: Any
) -> AsyncGenerator[DuosidaDataUpdateCoordinator, None]:
    """Return a coordinator instance."""
    coord = DuosidaDataUpdateCoordinator(
        hass,
        mock_charger,
        scan_interval=10,
        device_id="03123456789012345678",
    )
    yield coord
    # Cleanup: unschedule any pending refreshes
    coord._unschedule_refresh()


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
    from homeassistant.exceptions import ConfigEntryNotReady

    # Make the charger raise an error
    coordinator.charger.connect = MagicMock(return_value=False)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


async def test_coordinator_set_max_current(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can set max current."""
    import asyncio

    # First refresh to get initial data
    await coordinator.async_config_entry_first_refresh()

    # Set max current
    result = await coordinator.async_set_max_current(20)
    assert result is True

    # Verify the setting was persisted
    assert coordinator.get_stored_setting("max_current") == 20

    # Wait for debounced refresh to complete
    await asyncio.sleep(1.0)  # Default REQUEST_REFRESH_DELAY is 0.5s
    await hass.async_block_till_done()


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
    import asyncio

    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_start_charging()
    assert result is True

    # Wait for debounced refresh to complete
    await asyncio.sleep(1.0)
    await hass.async_block_till_done()


async def test_coordinator_stop_charging(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can stop charging."""
    import asyncio

    await coordinator.async_config_entry_first_refresh()

    result = await coordinator.async_stop_charging()
    assert result is True

    # Wait for debounced refresh to complete
    await asyncio.sleep(1.0)
    await hass.async_block_till_done()


async def test_coordinator_energy_integration(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator integrates power to calculate total energy."""
    await coordinator.async_config_entry_first_refresh()

    # Get initial energy
    initial_energy = coordinator.data["total_energy"]

    # Manually simulate a time delta and power consumption
    # Set last update to 1 hour ago (3600 seconds)
    current_time = hass.loop.time()
    coordinator._stored_settings["last_update_time"] = current_time - 3600.0
    coordinator._stored_settings["last_power"] = 11040.0  # 11.04 kW
    coordinator._stored_settings["total_energy"] = initial_energy

    # Set charger to still be at 11.04 kW
    coordinator.charger._status["power"] = 11040

    # Do another update - should integrate the power over the 1-hour gap
    await coordinator._async_update_data()
    energy_after_update = coordinator.data["total_energy"]

    # Energy should have increased
    # 11.04 kW * 1 hour = 11.04 kWh (approximately)
    assert energy_after_update > initial_energy
    # Should be roughly 11 kWh more (11040W * 1h / 1000 = 11.04 kWh)
    assert energy_after_update - initial_energy > 10.0


async def test_coordinator_reset_total_energy(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator can reset total energy."""
    import asyncio

    await coordinator.async_config_entry_first_refresh()

    # Set some energy value
    coordinator._stored_settings["total_energy"] = 100.0

    # Reset
    await coordinator.async_reset_total_energy()

    assert coordinator.get_stored_setting("total_energy") == 0.0

    # Wait for debounced refresh to complete
    await asyncio.sleep(1.0)
    await hass.async_block_till_done()


async def test_coordinator_settings_persistence(
    hass: HomeAssistant,
    coordinator: DuosidaDataUpdateCoordinator,
) -> None:
    """Test coordinator persists settings to storage."""
    import asyncio

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

    # Wait for all debounced refreshes to complete (3 calls debounced into 1)
    await asyncio.sleep(1.0)
    await hass.async_block_till_done()


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
    """Test coordinator disconnect is a no-op since connections are not persistent."""
    await coordinator.async_config_entry_first_refresh()

    # After refresh, charger should be disconnected (coordinator disconnects after each poll)
    assert coordinator.charger._connected is False

    # Disconnect is a no-op
    coordinator.disconnect()

    # Charger should still be disconnected
    assert coordinator.charger._connected is False
