"""Test Duosida EV integration setup and unload."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev import async_setup_entry, async_unload_entry
from custom_components.duosida_ev.const import DOMAIN

from .conftest import MOCK_CONFIG_ENTRY_DATA


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test setting up a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Mock the coordinator's methods
    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify the entry is loaded
    assert mock_config_entry.state == ConfigEntryState.LOADED

    # Verify the coordinator was created and stored
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    assert "coordinator" in hass.data[DOMAIN][mock_config_entry.entry_id]


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test setup entry fails when connection to charger fails."""
    mock_config_entry.add_to_hass(hass)

    # Mock connection failure
    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        side_effect=Exception("Connection failed"),
    ):
        assert not await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    # Setup the integration
    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    # Unload the integration
    assert await async_unload_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    # Verify the entry is unloaded
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED

    # Verify data was cleaned up
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_platforms_are_loaded(
    hass: HomeAssistant,
    mock_config_entry,
    mock_duosida_charger,
) -> None:
    """Test that all platforms are loaded."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_load_stored_settings",
        return_value=None,
    ), patch(
        "custom_components.duosida_ev.DuosidaDataUpdateCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=None,
    ) as mock_forward:
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        # Verify platforms were loaded
        assert mock_forward.called
        # Should load sensor, switch, number, button platforms
        loaded_platforms = mock_forward.call_args[0][1]
        assert "sensor" in loaded_platforms
        assert "switch" in loaded_platforms
        assert "number" in loaded_platforms
        assert "button" in loaded_platforms
