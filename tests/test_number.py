"""Test Duosida EV number entities."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_max_current_number(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test max charging current number entity."""
    # Check max current number entity exists
    max_current = hass.states.get("number.duosida_ev_charger_max_charging_current")
    assert max_current is not None

    # Check range
    assert max_current.attributes["min"] == 6
    assert max_current.attributes["max"] == 32
    assert max_current.attributes["step"] == 1


async def test_max_current_set_value(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test setting max current value."""
    with patch(
        "custom_components.duosida_ev.coordinator.DuosidaDataUpdateCoordinator.async_set_max_current",
        return_value=True,
    ) as mock_set:
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
    setup_integration: Any,
) -> None:
    """Test LED brightness number entity."""
    # LED brightness is disabled by default
    led_brightness = hass.states.get("number.duosida_ev_charger_led_brightness")
    assert led_brightness is None  # Disabled by default


async def test_max_voltage_number(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test max voltage number entity."""
    # Max voltage is disabled by default
    max_voltage = hass.states.get("number.duosida_ev_charger_max_voltage")
    assert max_voltage is None  # Disabled by default


async def test_min_voltage_number(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test min voltage number entity."""
    # Min voltage is disabled by default
    min_voltage = hass.states.get("number.duosida_ev_charger_min_voltage")
    assert min_voltage is None  # Disabled by default
