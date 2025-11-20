"""Test Duosida EV number entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.const import DOMAIN


async def test_max_current_number(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test max charging current number entity."""
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

    # Check max current number entity exists
    max_current = hass.states.get(f"number.duosida_ev_charger_max_charging_current")
    assert max_current is not None

    # Check range
    assert max_current.attributes["min"] == 6
    assert max_current.attributes["max"] == 32
    assert max_current.attributes["step"] == 1


async def test_max_current_set_value(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test setting max current value."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_set_max_current",
        return_value=True,
    ) as mock_set:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Set value
        await hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": "number.duosida_ev_charger_max_charging_current",
                "value": 20,
            },
            blocking=True,
        )

        # Verify async_set_max_current was called with correct value
        mock_set.assert_called_once_with(20)


async def test_led_brightness_number(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test LED brightness number entity."""
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

    # LED brightness is disabled by default
    led_brightness = hass.states.get(f"number.duosida_ev_charger_led_brightness")
    assert led_brightness is None  # Disabled by default


async def test_max_voltage_number(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test max voltage number entity."""
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

    # Max voltage is disabled by default
    max_voltage = hass.states.get(f"number.duosida_ev_charger_max_voltage")
    assert max_voltage is None  # Disabled by default


async def test_min_voltage_number(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test min voltage number entity."""
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

    # Min voltage is disabled by default
    min_voltage = hass.states.get(f"number.duosida_ev_charger_min_voltage")
    assert min_voltage is None  # Disabled by default
