"""Test Duosida EV switches."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.const import DOMAIN


async def test_charging_switch(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test charging switch."""
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

    # Check charging switch exists
    charging_switch = hass.states.get(f"switch.duosida_ev_charger_charging")
    assert charging_switch is not None

    # conn_status 2 = charging, so switch should be ON
    assert charging_switch.state == "on"


async def test_charging_switch_turn_on(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test turning on charging switch."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_start_charging",
        return_value=True,
    ) as mock_start:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Turn on the switch
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.duosida_ev_charger_charging"},
            blocking=True,
        )

        # Verify start_charging was called
        mock_start.assert_called_once()


async def test_charging_switch_turn_off(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test turning off charging switch."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_stop_charging",
        return_value=True,
    ) as mock_stop:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Turn off the switch
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": "switch.duosida_ev_charger_charging"},
            blocking=True,
        )

        # Verify stop_charging was called
        mock_stop.assert_called_once()


async def test_direct_mode_switch(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test direct mode switch."""
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

    # Check direct mode switch exists
    direct_mode_switch = hass.states.get(f"switch.duosida_ev_charger_direct_mode")
    assert direct_mode_switch is not None

    # Should be unknown initially (unknown-first approach)
    assert direct_mode_switch.state == "unknown"


async def test_stop_on_disconnect_switch(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test stop on disconnect switch."""
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

    # Check stop on disconnect switch exists
    stop_switch = hass.states.get(f"switch.duosida_ev_charger_stop_on_disconnect")
    assert stop_switch is not None

    # Should be unknown initially (unknown-first approach)
    assert stop_switch.state == "unknown"
