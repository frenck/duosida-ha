"""Test Duosida EV button entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.const import DOMAIN


async def test_start_charging_button(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test start charging button."""
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

    # Start charging button is disabled by default
    start_button = hass.states.get(f"button.duosida_ev_charger_start_charging")
    assert start_button is None  # Disabled by default


async def test_stop_charging_button(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test stop charging button."""
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

    # Stop charging button is disabled by default
    stop_button = hass.states.get(f"button.duosida_ev_charger_stop_charging")
    assert stop_button is None  # Disabled by default


async def test_reset_energy_button(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test reset total energy button."""
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

    # Reset energy button should exist
    reset_button = hass.states.get(f"button.duosida_ev_charger_reset_total_energy")
    assert reset_button is not None


async def test_reset_energy_button_press(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test pressing reset energy button."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_reset_total_energy",
        return_value=None,
    ) as mock_reset:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press the button
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.duosida_ev_charger_reset_total_energy"},
            blocking=True,
        )

        # Verify async_reset_total_energy was called
        mock_reset.assert_called_once()
