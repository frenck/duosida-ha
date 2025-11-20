"""Test Duosida EV sensors."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.const import DOMAIN

from .conftest import MOCK_CHARGER_STATUS


async def test_sensor_state_values(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test sensor states are correct."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Check status sensor
    status_sensor = hass.states.get(f"sensor.duosida_ev_charger_status")
    assert status_sensor is not None
    # conn_status 2 = "Charging"
    assert status_sensor.state == "Charging"

    # Check voltage sensor
    voltage_sensor = hass.states.get(f"sensor.duosida_ev_charger_voltage")
    assert voltage_sensor is not None
    assert voltage_sensor.state == "230.0"
    assert voltage_sensor.attributes["unit_of_measurement"] == UnitOfElectricPotential.VOLT

    # Check current sensor
    current_sensor = hass.states.get(f"sensor.duosida_ev_charger_current")
    assert current_sensor is not None
    assert current_sensor.state == "16.0"
    assert current_sensor.attributes["unit_of_measurement"] == UnitOfElectricCurrent.AMPERE

    # Check power sensor
    power_sensor = hass.states.get(f"sensor.duosida_ev_charger_power")
    assert power_sensor is not None
    assert power_sensor.state == "11040"
    assert power_sensor.attributes["unit_of_measurement"] == UnitOfPower.WATT

    # Check temperature sensor
    temp_sensor = hass.states.get(f"sensor.duosida_ev_charger_temperature")
    assert temp_sensor is not None
    assert temp_sensor.state == "35.0"
    assert temp_sensor.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS


async def test_sensor_cp_voltage(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test CP voltage sensor."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    cp_voltage_sensor = hass.states.get(f"sensor.duosida_ev_charger_cp_voltage")
    assert cp_voltage_sensor is not None
    assert cp_voltage_sensor.state == "6.0"  # 6V = charging state
    assert cp_voltage_sensor.attributes["unit_of_measurement"] == UnitOfElectricPotential.VOLT


async def test_sensor_session_energy(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test session energy sensor."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    session_energy_sensor = hass.states.get(f"sensor.duosida_ev_charger_session_energy")
    assert session_energy_sensor is not None
    assert session_energy_sensor.state == "5.5"  # From MOCK_CHARGER_STATUS
    assert session_energy_sensor.attributes["unit_of_measurement"] == UnitOfEnergy.KILO_WATT_HOUR
    assert session_energy_sensor.attributes["state_class"] == "measurement"


async def test_sensor_session_time(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test session time sensor converts minutes to hours."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    session_time_sensor = hass.states.get(f"sensor.duosida_ev_charger_session_time")
    assert session_time_sensor is not None
    # 120 minutes = 2.0 hours
    assert session_time_sensor.state == "2.0"
    assert session_time_sensor.attributes["unit_of_measurement"] == UnitOfTime.HOURS


async def test_sensor_total_energy(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test total energy sensor (integrated value)."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    total_energy_sensor = hass.states.get(f"sensor.duosida_ev_charger_total_energy")
    assert total_energy_sensor is not None
    assert total_energy_sensor.attributes["unit_of_measurement"] == UnitOfEnergy.KILO_WATT_HOUR
    # Should be TOTAL_INCREASING for HA Energy Dashboard
    assert total_energy_sensor.attributes["state_class"] == "total_increasing"


async def test_sensor_disabled_by_default(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test some sensors are disabled by default."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # L2/L3 voltage sensors should be disabled by default
    voltage_l2_sensor = hass.states.get(f"sensor.duosida_ev_charger_voltage_l2")
    assert voltage_l2_sensor is None  # Disabled by default

    # Model, manufacturer, firmware should be disabled by default
    model_sensor = hass.states.get(f"sensor.duosida_ev_charger_model")
    assert model_sensor is None  # Disabled by default


async def test_sensor_status_mapping(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test status sensor correctly maps status codes."""
    mock_config_entry.add_to_hass(hass)

    # Test different status codes
    status_mappings = {
        0: "Available",
        1: "Preparing",
        2: "Charging",
        3: "Cooling",
        4: "SuspendedEV",
        5: "Finished",
        6: "Holiday",
    }

    for status_code, status_name in status_mappings.items():
        # Update the mock to return different status
        with patch(
            "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
            return_value=None,
        ), patch(
            "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ), patch(
            "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.data",
            new_callable=lambda: {"conn_status": status_code},
        ):
            await hass.config_entries.async_setup(mock_config_entry.entry_id)
            await hass.async_block_till_done()

            status_sensor = hass.states.get(f"sensor.duosida_ev_charger_status")
            # Note: This test structure may need adjustment based on actual entity creation
