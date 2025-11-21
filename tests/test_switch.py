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
    charging_switch = hass.states.get(
        "switch.duosida_ev_charger_192_168_1_100_charging"
    )
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
            {"entity_id": "switch.duosida_ev_charger_192_168_1_100_charging"},
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
            {"entity_id": "switch.duosida_ev_charger_192_168_1_100_charging"},
            blocking=True,
        )

        # Verify stop_charging was called
        mock_stop.assert_called_once()


async def test_direct_mode_switch(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test direct mode switch."""
    # Check direct mode switch exists (disabled by default)
    direct_mode_switch = hass.states.get(
        "switch.duosida_ev_charger_192_168_1_100_direct_mode"
    )
    assert direct_mode_switch is None  # Disabled by default


async def test_stop_on_disconnect_switch(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test stop on disconnect switch."""
    # Check stop on disconnect switch exists (disabled by default)
    stop_switch = hass.states.get(
        "switch.duosida_ev_charger_192_168_1_100_stop_session_on_vehicle_disconnect"
    )
    assert stop_switch is None  # Disabled by default


async def test_charging_switch_with_no_data(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test charging switch property when coordinator has no data."""
    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN
    from custom_components.duosida_ev.switch import DuosidaChargingSwitch

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a switch instance directly
    switch = DuosidaChargingSwitch(coordinator, "03123456789012345678")

    # Test is_on when coordinator.data is None
    coordinator.data = None
    assert switch.is_on is False


async def test_direct_mode_switch_property(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test direct mode switch property reads from stored settings."""
    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN
    from custom_components.duosida_ev.switch import DuosidaDirectModeSwitch

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a switch instance directly
    switch = DuosidaDirectModeSwitch(coordinator, "03123456789012345678")

    # Test is_on reads from stored settings (should be None initially)
    value = switch.is_on
    assert value is None or isinstance(value, bool)


async def test_stop_on_disconnect_switch_property(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test stop on disconnect switch property reads from stored settings."""
    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN
    from custom_components.duosida_ev.switch import DuosidaStopOnDisconnectSwitch

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a switch instance directly
    switch = DuosidaStopOnDisconnectSwitch(coordinator, "03123456789012345678")

    # Test is_on reads from stored settings (should be None initially)
    value = switch.is_on
    assert value is None or isinstance(value, bool)


async def test_direct_mode_switch_async_methods(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test direct mode switch async turn on/off methods."""
    from unittest.mock import patch

    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN
    from custom_components.duosida_ev.switch import DuosidaDirectModeSwitch

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a switch instance directly
    switch = DuosidaDirectModeSwitch(coordinator, "03123456789012345678")
    switch.hass = hass

    # Test turn_on with success
    with (
        patch.object(coordinator, "async_set_direct_mode", return_value=True),
        patch.object(switch, "async_write_ha_state") as mock_write,
    ):
        await switch.async_turn_on()
        mock_write.assert_called_once()

    # Test turn_off with success
    with (
        patch.object(coordinator, "async_set_direct_mode", return_value=True),
        patch.object(switch, "async_write_ha_state") as mock_write,
    ):
        await switch.async_turn_off()
        mock_write.assert_called_once()


async def test_stop_on_disconnect_switch_async_methods(
    hass: HomeAssistant,
    setup_integration: Any,
) -> None:
    """Test stop on disconnect switch async turn on/off methods."""
    from unittest.mock import patch

    from custom_components.duosida_ev.const import COORDINATOR, DOMAIN
    from custom_components.duosida_ev.switch import DuosidaStopOnDisconnectSwitch

    # Get coordinator
    coordinator = hass.data[DOMAIN][setup_integration.entry_id][COORDINATOR]

    # Create a switch instance directly
    switch = DuosidaStopOnDisconnectSwitch(coordinator, "03123456789012345678")
    switch.hass = hass

    # Test turn_on with success
    with (
        patch.object(coordinator, "async_set_stop_on_disconnect", return_value=True),
        patch.object(switch, "async_write_ha_state") as mock_write,
    ):
        await switch.async_turn_on()
        mock_write.assert_called_once()

    # Test turn_off with success
    with (
        patch.object(coordinator, "async_set_stop_on_disconnect", return_value=True),
        patch.object(switch, "async_write_ha_state") as mock_write,
    ):
        await switch.async_turn_off()
        mock_write.assert_called_once()
