# Duosida EV Charger - Home Assistant Integration

## Project Overview

Home Assistant custom integration for **local control** of Duosida EV wall chargers. Communicates directly with the charger over TCP (port 9988), bypassing cloud services.

Uses the `duosida-ev` Python library (PyPI) for low-level communication.

## Project Structure

```
duosida-ha/
├── custom_components/
│   └── duosida_ev/
│       ├── __init__.py          # Entry point, setup/unload
│       ├── config_flow.py       # Setup wizard UI
│       ├── coordinator.py       # Data fetching, settings persistence
│       ├── const.py             # Constants, status codes
│       ├── entity.py            # Base entity class
│       ├── sensor.py            # Read-only sensors
│       ├── switch.py            # Charging, direct mode switches
│       ├── number.py            # Max current, LED brightness sliders
│       ├── button.py            # Start/stop buttons
│       ├── manifest.json        # Integration metadata
│       ├── strings.json         # UI strings
│       └── translations/
│           └── en.json          # English translations
├── hacs.json                    # HACS metadata
├── README.md                    # User documentation
├── LICENSE                      # MIT license
└── CLAUDE.md                    # This file
```

## Key Concepts

### Home Assistant Integration Architecture

1. **Config Entry**: User's configuration (IP, device ID, scan interval)
2. **Coordinator**: Central data fetcher, called every scan_interval
3. **Platforms**: Entity types (sensor, switch, number, button)
4. **Entities**: Individual controls/sensors shown in UI

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
Every 10 seconds: coordinator fetches new data, entities update automatically
```

### Coordinator Pattern

The coordinator (`DuosidaDataUpdateCoordinator`) is critical:
- **Single connection** to charger (not one per entity)
- **Periodic polling** via `_async_update_data()`
- **Shared data** via `self.data` dictionary
- **Settings persistence** via Home Assistant's `Store`

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

**Location in code:**
- Integration: `coordinator.py` in `_async_update_data()` (lines 249-283)
- Reset method: `coordinator.py` `async_reset_total_energy()`
- Sensor definition: `sensor.py` total_energy sensor (lines 188-199)

## Sensors

**Order:** Sensors are ordered to match the duosida-ev library's `to_dict()` output for consistency.

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

## Controls

| Entity | Type | Description |
|--------|------|-------------|
| Charging | Switch | Start/stop charging (reads conn_status == 2) |
| Direct Mode | Switch | Plug-and-charge mode (stored setting) |
| Max Charging Current | Number | 6-32A slider |
| LED Brightness | Number | 0, 1, 3 (not 2!) slider (disabled by default) |
| Max Voltage | Number | 265-290V slider (disabled by default) |
| Min Voltage | Number | 70-110V slider (disabled by default) |
| Start Charging | Button | Send start command (disabled by default) |
| Stop Charging | Button | Send stop command (disabled by default) |
| Reset Total Energy | Button | Reset total energy counter to zero |

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

## Dependencies

- **duosida-ev** (PyPI): TCP communication with charger
- **Home Assistant Core**: 2023.1+
- **Python**: 3.10+

## Development

### Testing Locally

1. Copy `custom_components/duosida_ev` to your HA config
2. Restart Home Assistant
3. Add integration via UI
4. Check logs: Settings → System → Logs → filter "duosida"

### Key Files to Modify

- **Add new sensor**: Edit `sensor.py` SENSORS tuple
- **Add new control**: Create entity class in appropriate platform file
- **Change defaults**: Edit `const.py`
- **Add stored setting**: Update coordinator's `_stored_settings` dict and sync method

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

## Configuration

**Default values:**
- Port: 9988
- Scan interval: 10 seconds
- LED brightness: 3 (high)
- Direct mode: False (disabled)

**Config flow options:**
- Auto-discovery (UDP broadcast)
- Manual entry (IP, port, device ID, scan interval)

## Notes

- Device ID is 19 digits starting with "03"
- LED brightness only accepts 0, 1, 3 (not 2)
- Direct mode = plug-and-charge (auto-start when vehicle connected)
- Charger uses protobuf over TCP
- Discovery uses UDP broadcast on ports 48890/48899

## Troubleshooting

**Entity shows "Unavailable":**
- Check charger is on network
- Check TCP port 9988 is accessible
- Look at HA logs for connection errors

**Settings don't persist:**
- Check `.storage/duosida_ev.*` file exists
- Look for storage errors in logs

**Values seem wrong:**
- Enable debug logging: `logger.duosida_ev: debug`
- Check raw data in coordinator

## Related Projects

- **duosida-ev** (PyPI): Python library for charger communication
- **jello1974/duosidaEV-home-assistant**: Cloud-based HA integration (inspiration)
