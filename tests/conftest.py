"""Fixtures for Duosida EV integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.duosida_ev.const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

pytest_plugins = "pytest_homeassistant_custom_component"


# Mock data - realistic charger status
MOCK_CHARGER_STATUS = {
    "conn_status": 2,  # Charging
    "cp_voltage": 6.0,  # 6V = charging
    "voltage": 230.0,  # L1 voltage
    "voltage_l2": 230.0,
    "voltage_l3": 230.0,
    "current": 16.0,  # 16A charging current
    "current_l2": 16.0,
    "current_l3": 16.0,
    "power": 11040,  # 3 * 230V * 16A
    "temperature": 35.0,  # 35°C
    "session_energy": 5.5,  # 5.5 kWh this session
    "session_time": 120,  # 120 minutes = 2 hours
    "model": "SmartChargePI",
    "manufacturer": "Duosida",
    "firmware": "1.0.0",
}

# Mock configuration entry data
MOCK_CONFIG_ENTRY_DATA = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: DEFAULT_PORT,
    CONF_DEVICE_ID: "03123456789012345678",
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}

# Mock discovered charger
MOCK_DISCOVERED_CHARGER = {
    "ip": "192.168.1.100",
    "port": 9988,
    "device_id": "03123456789012345678",
    "model": "SmartChargePI",
}


class MockDuosidaCharger:
    """Mock DuosidaCharger for testing."""

    def __init__(
        self, host: str, port: int = 9988, device_id: str = "", debug: bool = False
    ):
        """Initialize mock charger."""
        self.host = host
        self.port = port
        self.device_id = device_id
        self.debug = debug
        self._connected = False
        self._status = MOCK_CHARGER_STATUS.copy()

    def connect(self) -> bool:
        """Mock connect."""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Mock disconnect."""
        self._connected = False

    def get_status(self):
        """Mock get_status - returns self (charger object)."""
        if not self._connected:
            raise ConnectionError("Not connected")
        return self  # Return self so to_dict() can be called on the result

    def to_dict(self) -> dict:
        """Mock to_dict."""
        if not self._connected:
            raise ConnectionError("Not connected")
        return self._status

    def start_charging(self) -> bool:
        """Mock start_charging."""
        if not self._connected:
            return False
        self._status["conn_status"] = 2  # Charging
        return True

    def stop_charging(self) -> bool:
        """Mock stop_charging."""
        if not self._connected:
            return False
        self._status["conn_status"] = 0  # Available
        return True

    def set_max_current(self, current: int) -> bool:
        """Mock set_max_current."""
        if not self._connected:
            return False
        if not 6 <= current <= 32:
            return False
        self._status["current"] = float(current)
        return True

    def set_led_brightness(self, brightness: int) -> bool:
        """Mock set_led_brightness."""
        if not self._connected:
            return False
        if brightness not in (0, 1, 3):
            return False
        return True

    def set_direct_mode(self, enabled: bool) -> bool:
        """Mock set_direct_mode."""
        if not self._connected:
            return False
        return True

    def set_stop_on_disconnect(self, enabled: bool) -> bool:
        """Mock set_stop_on_disconnect."""
        if not self._connected:
            return False
        return True

    def set_max_voltage(self, voltage: int) -> bool:
        """Mock set_max_voltage."""
        if not self._connected:
            return False
        if not 265 <= voltage <= 290:
            return False
        return True

    def set_min_voltage(self, voltage: int) -> bool:
        """Mock set_min_voltage."""
        if not self._connected:
            return False
        if not 70 <= voltage <= 110:
            return False
        return True


@pytest.fixture
def mock_charger() -> MockDuosidaCharger:
    """Return a mock charger instance."""
    return MockDuosidaCharger(
        host="192.168.1.100",
        port=9988,
        device_id="03123456789012345678",
    )


@pytest.fixture
def mock_duosida_charger() -> Generator[MagicMock, None, None]:
    """Mock the DuosidaCharger class."""
    with patch(
        "custom_components.duosida_ev.DuosidaCharger",
        return_value=MockDuosidaCharger(
            host="192.168.1.100",
            port=9988,
            device_id="03123456789012345678",
        ),
    ) as mock:
        yield mock


@pytest.fixture
def mock_duosida_charger_in_coordinator() -> Generator[MagicMock, None, None]:
    """Mock the DuosidaCharger class in coordinator."""
    with patch(
        "custom_components.duosida_ev.coordinator.DuosidaCharger",
        return_value=MockDuosidaCharger(
            host="192.168.1.100",
            port=9988,
            device_id="03123456789012345678",
        ),
    ) as mock:
        yield mock


@pytest.fixture
def mock_duosida_charger_in_config_flow() -> Generator[MagicMock, None, None]:
    """Mock the DuosidaCharger class in config flow."""
    with patch(
        "custom_components.duosida_ev.config_flow.DuosidaCharger",
        return_value=MockDuosidaCharger(
            host="192.168.1.100",
            port=9988,
            device_id="03123456789012345678",
        ),
    ) as mock:
        yield mock


@pytest.fixture
def mock_discover_chargers() -> Generator[MagicMock, None, None]:
    """Mock discover_chargers function."""
    with patch(
        "custom_components.duosida_ev.config_flow.discover_chargers",
        return_value=[MOCK_DISCOVERED_CHARGER],
    ) as mock:
        yield mock


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock setup entry."""
    with patch(
        "custom_components.duosida_ev.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Duosida EV Charger",
        data=MOCK_CONFIG_ENTRY_DATA,
        source="user",
        entry_id="test_entry_id",
        unique_id="03123456789012345678",
    )
