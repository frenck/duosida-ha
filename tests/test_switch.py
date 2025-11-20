"""Test Duosida EV switches."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_charging_switch(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test charging switch."""
    # Check charging switch exists
    charging_switch = hass.states.get("switch.duosida_ev_charger_charging")
    assert charging_switch is not None

    # conn_status 2 = charging, so switch should be ON
    assert charging_switch.state == "on"


async def test_charging_switch_turn_on(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test turning on charging switch."""
    with patch(
        "custom_components.duosida_ev.coordinator.DuosidaDataUpdateCoordinator.async_start_charging",
        return_value=True,
    ) as mock_start:
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
    setup_integration: Any,
) -> None:
    """Test turning off charging switch."""
    with patch(
        "custom_components.duosida_ev.coordinator.DuosidaDataUpdateCoordinator.async_stop_charging",
        return_value=True,
    ) as mock_stop:
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
    setup_integration: Any,
) -> None:
    """Test direct mode switch."""
    # Check direct mode switch exists
    direct_mode_switch = hass.states.get("switch.duosida_ev_charger_direct_mode")
    assert direct_mode_switch is not None

    # Should be unknown initially (unknown-first approach)
    assert direct_mode_switch.state == "unknown"


async def test_stop_on_disconnect_switch(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test stop on disconnect switch."""
    # Check stop on disconnect switch exists
    stop_switch = hass.states.get("switch.duosida_ev_charger_stop_on_disconnect")
    assert stop_switch is not None

    # Should be unknown initially (unknown-first approach)
    assert stop_switch.state == "unknown"
