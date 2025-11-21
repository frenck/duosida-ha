---
title: Duosida EV Charger
description: Instructions on how to integrate Duosida EV wall chargers with Home Assistant for local control.
ha_category:
  - Car
ha_release: "2025.1"
ha_iot_class: Local Polling
ha_domain: duosida_ev
ha_platforms:
  - binary_sensor
  - button
  - number
  - sensor
  - switch
ha_config_flow: true
ha_codeowners:
  - "@americodias"
ha_integration_type: device
---

The **Duosida EV Charger** integration allows you to monitor and control your Duosida EV wall charger directly over your local network, without requiring any cloud connection.

This integration communicates with the charger via TCP on port 9988, providing complete local control and fast response times.

{% include integrations/config_flow.md %}

## Prerequisites

- Duosida EV wall charger (SmartChargePI series)
- Charger connected to your local network
- Device ID (19 digits starting with "03") - found in the official Duosida app or on the charger label

## Setup

The integration can be set up in two ways:

### Auto-discovery

1. Select **Discover chargers on network** during setup
2. The integration will scan your network using UDP broadcast
3. Select your charger from the list of discovered devices
4. The integration will automatically configure the connection

### Manual configuration

1. Deselect the discovery option during setup
2. Enter the charger's IP address
3. Enter the device ID (19 digits starting with "03")
4. Optionally adjust the port (default: 9988) and scan interval (default: 10 seconds)

## Sensors

The integration provides the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| Status | Current charger status (Available, Preparing, Charging, etc.) | - |
| CP Voltage | Control Pilot voltage reading | V |
| Voltage | L1 voltage | V |
| Voltage L2 | L2 voltage (disabled by default) | V |
| Voltage L3 | L3 voltage (disabled by default) | V |
| Current | L1 current | A |
| Current L2 | L2 current (disabled by default) | A |
| Current L3 | L3 current (disabled by default) | A |
| Power | Instantaneous power consumption | W |
| Temperature | Charger temperature | °C |
| Session Energy | Energy consumed in current session | kWh |
| Session Time | Duration of current charging session | h |
| Total Energy | Cumulative energy consumption (integrated) | kWh |
| Model | Charger model (disabled by default) | - |
| Manufacturer | Charger manufacturer (disabled by default) | - |
| Firmware | Firmware version (disabled by default) | - |

### Total Energy sensor

The **Total Energy** sensor calculates cumulative energy consumption by integrating power readings over time. This value:

- Persists across Home Assistant restarts
- Is compatible with the Energy Dashboard
- Can be reset using the **Reset Total Energy** button

## Controls

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| Charging | Shows if the charger is currently charging (read-only) |

### Switches

| Switch | Description |
|--------|-------------|
| Charging | Start or stop charging (with debounce to prevent UI bounce) |
| Direct Mode | Enable plug-and-charge mode (disabled by default) |
| Stop on Disconnect | Stop session when vehicle disconnects (disabled by default) |

### Numbers

| Number | Description | Range |
|--------|-------------|-------|
| Max Charging Current | Maximum charging current | 6-32 A |
| LED Brightness | Charger LED brightness (disabled by default) | 0, 1, 3 |
| Max Voltage | Maximum voltage threshold (disabled by default) | 265-290 V |
| Min Voltage | Minimum voltage threshold (disabled by default) | 70-110 V |

### Buttons

| Button | Description |
|--------|-------------|
| Start Charging | Send start command to begin charging |
| Stop Charging | Send stop command to halt charging |
| Reset Total Energy | Reset the cumulative energy counter to zero |

## Status codes

The charger reports the following status codes:

| Code | Status | Description |
|------|--------|-------------|
| 0 | Available | Ready to charge |
| 1 | Preparing | Vehicle connected, preparing to charge |
| 2 | Charging | Actively charging |
| 3 | Cooling | Cooling down after charging |
| 4 | SuspendedEV | Charging suspended by vehicle |
| 5 | Finished | Charging complete |
| 6 | Holiday | Holiday mode active |

## Options

After initial setup, you can reconfigure the integration by selecting **Configure** on the integration card. The following options are available:

| Option | Description | Default |
|--------|-------------|---------|
| Scan interval | How often to poll the charger for updates (seconds) | 10 |
| Switch debounce | How long to hold switch state after sending command (seconds) | 30 |

The **switch debounce** option prevents the charging switch from bouncing between states during charge start/stop transitions. The charger takes time to transition between states (e.g., Available → Preparing → Charging), and the debounce ensures the UI shows a stable state.

## Example automations

### Start charging during off-peak hours

```yaml
automation:
  - alias: "Start EV charging at off-peak"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: sensor.duosida_ev_charger_status
        state: "Preparing"
    action:
      - service: button.press
        target:
          entity_id: button.duosida_ev_charger_start_charging
```

### Stop charging when reaching energy limit

```yaml
automation:
  - alias: "Stop charging at 30 kWh"
    trigger:
      - platform: numeric_state
        entity_id: sensor.duosida_ev_charger_session_energy
        above: 30
    action:
      - service: button.press
        target:
          entity_id: button.duosida_ev_charger_stop_charging
```

### Adjust charging current based on solar production

```yaml
automation:
  - alias: "Solar-aware charging"
    trigger:
      - platform: state
        entity_id: sensor.solar_power
    action:
      - service: number.set_value
        target:
          entity_id: number.duosida_ev_charger_max_charging_current
        data:
          value: >
            {% set solar = states('sensor.solar_power') | float(0) %}
            {% set current = (solar / 230) | int %}
            {{ [32, [6, current] | max] | min }}
```

## Troubleshooting

### Cannot connect to charger

- Verify the charger is powered on and connected to your network
- Ensure the IP address is correct
- Check that TCP port 9988 is not blocked by your firewall
- Try pinging the charger from your Home Assistant host

### Entity shows "Unavailable"

- The charger may be temporarily unreachable
- Check network connectivity
- Review Home Assistant logs for connection errors

### Settings don't persist after restart

- Ensure Home Assistant has write access to the `.storage` directory
- Check logs for storage-related errors

### Discovery doesn't find any chargers

- Ensure the charger is on the same network/VLAN as Home Assistant
- UDP broadcast on ports 48890/48899 must be allowed
- Try manual configuration instead

### Values seem incorrect

- Enable debug logging to see raw data from the charger:

```yaml
logger:
  logs:
    custom_components.duosida_ev: debug
```

## Known limitations

- The charger does not report back certain configuration values (LED brightness, direct mode, voltage thresholds). These are stored locally in Home Assistant after being set.
- Three-phase measurements (L2, L3) are available but disabled by default as most installations are single-phase.
- The LED brightness control only accepts values 0, 1, or 3 (not 2).

## Related integrations

This integration provides **local control** and does not require cloud connectivity. If you prefer cloud-based control, see the [Duosida](/integrations/duosida/) integration which connects via the manufacturer's cloud service.
