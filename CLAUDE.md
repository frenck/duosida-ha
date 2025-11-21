# Duosida EV Charger - Home Assistant Integration

## Project Overview

Home Assistant custom integration for **local control** of Duosida EV wall chargers. Communicates directly with the charger over TCP (port 9988), bypassing cloud services.

Uses the `duosida-ev` Python library (PyPI) for low-level communication.

**Status:** Gold Tier Complete - Ready for official Home Assistant submission!

## Project Structure

```
duosida-ha/
├── custom_components/
│   └── duosida_ev/
│       ├── __init__.py          # Entry point, setup/unload
│       ├── binary_sensor.py     # Charging status (read-only)
│       ├── button.py            # Start/stop/reset buttons
│       ├── config_flow.py       # Setup wizard + options flow
│       ├── const.py             # Constants, status codes
│       ├── coordinator.py       # Data fetching, settings persistence
│       ├── entity.py            # Base entity class
│       ├── number.py            # Max current, LED brightness sliders
│       ├── sensor.py            # Read-only sensors (17 total)
│       ├── switch.py            # Charging (with debounce), direct mode
│       ├── manifest.json        # Integration metadata
│       ├── strings.json         # UI strings
│       └── translations/        # 20 language translations
├── tests/                       # 68 tests, 96% coverage
│   ├── conftest.py              # Test fixtures
│   ├── test_binary_sensor.py
│   ├── test_button.py
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   ├── test_init.py
│   ├── test_number.py
│   ├── test_sensor.py
│   └── test_switch.py
├── htmlcov/                     # Coverage report
├── duosida_ev.markdown          # Official HA documentation
├── INTEGRATION_CHECKLIST.md     # Quality checklist
├── CONTRIBUTING.md              # Development guide
├── README.md                    # User documentation
├── LICENSE                      # MIT license
└── CLAUDE.md                    # This file
```

## Key Concepts

### Home Assistant Integration Architecture

1. **Config Entry**: User's configuration (IP, device ID, scan interval, switch debounce)
2. **Coordinator**: Central data fetcher, called every scan_interval
3. **Platforms**: Entity types (binary_sensor, sensor, switch, number, button)
4. **Entities**: Individual controls/sensors shown in UI (28 total)

### Data Flow

```
User adds integration
        ↓
config_flow.py → Creates ConfigEntry
        ↓
__init__.py → Creates Coordinator, loads stored settings
        ↓
coordinator.py → Connects to charger, syncs settings, fetches status
        ↓
sensor.py, switch.py, etc. → Create entities that read from coordinator.data
        ↓
Every scan_interval: coordinator fetches new data, entities update automatically
```

### Coordinator Pattern

The coordinator (`DuosidaDataUpdateCoordinator`) is critical:
- **Single connection** to charger (not one per entity)
- **Periodic polling** via `_async_update_data()`
- **Shared data** via `self.data` dictionary
- **Settings persistence** via Home Assistant's `Store`
- **Switch debounce** time stored for charging switch

All entities inherit from `CoordinatorEntity` which:
- Registers for updates automatically
- Provides `self.coordinator.data` to read values
- Handles availability (unavailable when coordinator fails)

## Important: Settings Persistence

**Problem**: The charger doesn't report back some configuration values:
- LED brightness
- Direct work mode
- Max/min voltage settings
- Stop on disconnect
- Total energy consumption (needs to be calculated)

**Solution**: Unknown-First Approach

1. **Initial state:** All settings start as `None` (unknown)
   - Integration does NOT assume any default values
   - Integration does NOT send any settings to charger on first connection
   - Charger retains its existing configuration

2. **When user changes a setting:**
   - Send command to charger immediately
   - Save value to HA storage
   - Entity shows the set value

3. **On HA restart:**
   - Load stored settings from `.storage/duosida_ev.{device_id}`
   - **Only sync settings that are not None** (i.e., user has explicitly set them)
   - Unknown settings remain unknown

4. **Entity display:**
   - Unknown settings show as "Unknown" in HA UI
   - User must explicitly set them to see/control the value
   - Once set, value persists across restarts

```python
# In coordinator.py
self._stored_settings = {
    "max_current": None,           # Unknown until user sets it
    "led_brightness": None,        # Unknown until user sets it
    "direct_mode": None,           # Unknown until user sets it
    "stop_on_disconnect": None,    # Unknown until user sets it
    "max_voltage": None,           # Unknown until user sets it
    "min_voltage": None,           # Unknown until user sets it
    "total_energy": 0.0,           # Calculated value, starts at 0
    "last_power": 0.0,
    "last_update_time": None,
}
```

**Key Principle:** The integration never makes assumptions about the charger's configuration. It only remembers what the user explicitly configures through Home Assistant.

## Charging Switch Debounce

**Problem**: The charger takes time to transition between states (Available → Preparing → Charging). Without debounce, the switch would bounce between ON/OFF during transitions.

**Solution**: Configurable debounce via options flow

```python
# In switch.py - DuosidaChargingSwitch
@property
def is_on(self) -> bool:
    # Check if we're in the debounce window
    if self._last_command_time is not None and self._optimistic_state is not None:
        elapsed = time.monotonic() - self._last_command_time
        if elapsed < self.coordinator.switch_debounce:
            return self._optimistic_state  # Return optimistic state
    # Return actual state from coordinator
    return self.coordinator.data.get("conn_status") == 2
```

**Flow:**
1. User clicks switch ON → Switch shows ON immediately (optimistic)
2. Command sent to charger
3. Coordinator updates ignored for `switch_debounce` seconds (default: 30)
4. After debounce period, switch syncs with actual charger state

**Configuration:** Options flow allows users to adjust debounce (5-120 seconds)

## Total Energy Integration

**How it works:**

The charger provides `session_energy` (current charging session only), but not total lifetime energy.
We calculate total energy by **integrating power over time** using the trapezoidal rule:

1. Every scan interval, we read `power` (W) and current time
2. Calculate: `energy_delta = average_power × time_delta / 1000` (convert W to kW)
3. Add to cumulative total: `total_energy += energy_delta`
4. Persist to storage for survival across restarts

**Formula:**
```
Energy (kWh) = [(P₁ + P₂) / 2] × Δt / 1000
```

Where:
- P₁ = previous power reading (W)
- P₂ = current power reading (W)
- Δt = time elapsed (hours)

**Features:**
- Always increasing (never resets automatically)
- Persisted across HA restarts
- Recognized by HA Energy Dashboard
- Can be manually reset via "Reset Total Energy" button
- Sanity checks prevent bad readings (max 100 kWh per interval)

## Entities (28 Total)

### Sensors (17)

| Key | Name | Unit | Notes |
|-----|------|------|-------|
| state | Status | - | Mapped from conn_status (0-6) |
| cp_voltage | CP Voltage | V | Control Pilot voltage reading |
| voltage | Voltage | V | L1 voltage |
| voltage_l2 | Voltage L2 | V | Disabled by default |
| voltage_l3 | Voltage L3 | V | Disabled by default |
| current | Current | A | L1 current |
| current_l2 | Current L2 | A | Disabled by default |
| current_l3 | Current L3 | A | Disabled by default |
| power | Power | W | Instantaneous power (V × I) |
| temperature | Temperature | °C | Charger station temperature |
| session_energy | Session Energy | kWh | Current session (from charger) |
| session_time | Session Time | h | Current session duration in hours |
| total_energy | Total Energy | kWh | **Integrated total energy** (always increasing) |
| model | Model | - | Device model (disabled by default) |
| manufacturer | Manufacturer | - | Device manufacturer (disabled by default) |
| firmware | Firmware | - | Firmware version (disabled by default) |
| cp_state | CP State | - | Control pilot state (disabled by default) |

### Binary Sensors (1)

| Entity | Description |
|--------|-------------|
| Charging | Shows if charger is currently charging (read-only status) |

### Switches (3)

| Entity | Description |
|--------|-------------|
| Charging | Start/stop charging (with debounce to prevent UI bounce) |
| Direct Mode | Plug-and-charge mode (disabled by default) |
| Stop on Disconnect | Stop session when vehicle disconnects (disabled by default) |

### Numbers (4)

| Entity | Range | Description |
|--------|-------|-------------|
| Max Charging Current | 6-32A | Maximum charging current |
| LED Brightness | 0, 1, 3 | LED brightness (disabled by default) |
| Max Voltage | 265-290V | Max voltage threshold (disabled by default) |
| Min Voltage | 70-110V | Min voltage threshold (disabled by default) |

### Buttons (3)

| Entity | Description |
|--------|-------------|
| Start Charging | Send start command (enabled by default) |
| Stop Charging | Send stop command (enabled by default) |
| Reset Total Energy | Reset total energy counter to zero |

## Status Codes

From `const.py`:

```python
STATUS_CODES = {
    0: "Available",
    1: "Preparing",
    2: "Charging",
    3: "Cooling",
    4: "SuspendedEV",
    5: "Finished",
    6: "Holiday",
}

CP_STATE_CODES = {
    0: "A - No vehicle",
    1: "B - Vehicle connected",
    2: "C - Charging",
    3: "D - Ventilation required",
    4: "E - Error",
    5: "F - Not available",
}
```

## Configuration

### Config Flow Options

| Option | Description | Default |
|--------|-------------|---------|
| Host | Charger IP address | (required) |
| Port | TCP port | 9988 |
| Device ID | 19-digit ID starting with "03" | (auto-detected) |
| Scan Interval | Polling interval in seconds | 10 |

### Options Flow (Reconfiguration)

| Option | Description | Range | Default |
|--------|-------------|-------|---------|
| Scan Interval | Polling interval | 5-300s | 10 |
| Switch Debounce | Charging switch debounce | 5-120s | 30 |

## Dependencies

- **duosida-ev** (PyPI): TCP communication with charger (v0.1.3)
- **Home Assistant Core**: 2023.1+
- **Python**: 3.10+

## Development

### Development Environment Setup

```bash
# Create virtual environment using uv
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux

# Install development dependencies
uv pip install -r requirements_dev.txt
# Or manually:
uv pip install ruff black mypy pytest pytest-homeassistant-custom-component pytest-cov

# Install the duosida-ev library
uv pip install duosida-ev==0.1.3
```

### Running Tests

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=custom_components.duosida_ev --cov-report=html

# Run specific test file
.venv/bin/python -m pytest tests/test_switch.py -v
```

### Code Quality Checks

```bash
# Run all checks
.venv/bin/ruff check .
.venv/bin/black --check .
.venv/bin/mypy custom_components/duosida_ev --ignore-missing-imports

# Auto-fix issues
.venv/bin/black .
.venv/bin/ruff check --fix .
```

### Testing Locally in Home Assistant

1. Copy `custom_components/duosida_ev` to your HA config
2. Restart Home Assistant
3. Add integration via UI
4. Check logs: Settings → System → Logs → filter "duosida"

### Key Files to Modify

- **Add new sensor**: Edit `sensor.py` SENSORS tuple
- **Add new control**: Create entity class in appropriate platform file
- **Change defaults**: Edit `const.py`
- **Add stored setting**: Update coordinator's `_stored_settings` dict and sync method
- **Add option**: Update `config_flow.py` OptionsFlowHandler

### Common Patterns

**Reading from coordinator data:**
```python
@property
def native_value(self):
    if not self.coordinator.data:
        return None
    return self.coordinator.data.get("key")
```

**Reading stored settings:**
```python
@property
def is_on(self):
    return self.coordinator.get_stored_setting("direct_mode") or False
```

**Sending command and persisting:**
```python
async def async_turn_on(self, **kwargs):
    if await self.coordinator.async_set_direct_mode(True):
        self.async_write_ha_state()  # Update UI immediately
```

**Running blocking code:**
```python
result = await self.hass.async_add_executor_job(
    self.charger.some_blocking_method, arg1, arg2
)
```

## Quality Metrics

| Metric | Value |
|--------|-------|
| Tests | 68/68 passing |
| Coverage | 96% |
| Languages | 20 translations |
| Entities | 28 total |
| Code Quality | ruff, black, mypy passing |

### Coverage Breakdown

| File | Coverage |
|------|----------|
| binary_sensor.py | 100% |
| const.py | 100% |
| entity.py | 100% |
| number.py | 100% |
| switch.py | 97% |
| __init__.py | 95% |
| button.py | 95% |
| coordinator.py | 95% |
| sensor.py | 94% |
| config_flow.py | 90% |

## Notes

- Device ID is 19 digits starting with "03"
- LED brightness only accepts 0, 1, 3 (not 2)
- Direct mode = plug-and-charge (auto-start when vehicle connected)
- Charger uses protobuf over TCP
- Discovery uses UDP broadcast on ports 48890/48899
- Charging switch has configurable debounce (default 30s) to prevent UI bounce

## Troubleshooting

**Entity shows "Unavailable":**
- Check charger is on network
- Check TCP port 9988 is accessible
- Look at HA logs for connection errors

**Charging switch bounces:**
- Increase switch debounce in integration options
- Default is 30 seconds, can be set up to 120 seconds

**Settings don't persist:**
- Check `.storage/duosida_ev.*` file exists
- Look for storage errors in logs

**Values seem wrong:**
- Enable debug logging: `logger.duosida_ev: debug`
- Check raw data in coordinator

## Related Projects

- **duosida-ev** (PyPI): Python library for charger communication
- **jello1974/duosidaEV-home-assistant**: Cloud-based HA integration (inspiration)
