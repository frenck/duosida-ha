"""Test Duosida EV button entities."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_start_charging_button(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test start charging button."""
    # Start charging button is disabled by default
    start_button = hass.states.get("button.duosida_ev_charger_start_charging")
    assert start_button is None  # Disabled by default


async def test_stop_charging_button(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test stop charging button."""
    # Stop charging button is disabled by default
    stop_button = hass.states.get("button.duosida_ev_charger_stop_charging")
    assert stop_button is None  # Disabled by default


async def test_reset_energy_button(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test reset total energy button."""
    # Reset energy button should exist
    reset_button = hass.states.get("button.duosida_ev_charger_reset_total_energy")
    assert reset_button is not None


async def test_reset_energy_button_press(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test pressing reset energy button."""
    with patch(
        "custom_components.duosida_ev.coordinator.DuosidaDataUpdateCoordinator.async_reset_total_energy",
        return_value=None,
    ) as mock_reset:
        # Press the button
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.duosida_ev_charger_reset_total_energy"},
            blocking=True,
        )

        # Verify async_reset_total_energy was called
        mock_reset.assert_called_once()
