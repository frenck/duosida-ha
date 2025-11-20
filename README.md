# Duosida EV Charger - Home Assistant Integration (Local Control)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for **local control** of Duosida EV wall chargers. This integration communicates directly with your charger over your local network, without requiring cloud services.

## Features

- **Local Control**: Direct TCP communication with your charger (no cloud dependency)
- **Auto-Discovery**: Automatically finds chargers on your network
- **Real-time Monitoring**: Voltage, current, power, temperature, energy consumption
- **Charging Control**: Start/stop charging, set max current (6-32A)
- **Configuration**: LED brightness, direct mode (plug and charge)
- **3-Phase Support**: Monitor all phases (L1, L2, L3)

## Sensors

All sensors update every 10 seconds (configurable).

| Sensor | Unit | Device Class | State Class | Description |
|--------|------|--------------|-------------|-------------|
| Status | - | - | - | Current charger state (Available, Preparing, Charging, Cooling, SuspendedEV, Finished, Holiday) |
| CP Voltage | V | voltage | measurement | Control Pilot voltage (indicates connection state) |
| Voltage (L1) | V | voltage | measurement | Line 1 voltage |
| Voltage L2* | V | voltage | measurement | Line 2 voltage (3-phase chargers) |
| Voltage L3* | V | voltage | measurement | Line 3 voltage (3-phase chargers) |
| Current (L1) | A | current | measurement | Line 1 charging current |
| Current L2* | A | current | measurement | Line 2 charging current (3-phase chargers) |
| Current L3* | A | current | measurement | Line 3 charging current (3-phase chargers) |
| Power | W | power | measurement | Instantaneous power consumption |
| Temperature | °C | temperature | measurement | Charger station temperature |
| Session Energy | kWh | energy | total_increasing | Energy consumed in current charging session |
| Session Time | h | duration | measurement | Duration of current charging session |
| Total Energy | kWh | energy | total_increasing | Total lifetime energy consumption (integrated from power readings) |
| Model* | - | - | - | Charger model name |
| Manufacturer* | - | - | - | Manufacturer name |
| Firmware* | - | - | - | Firmware version |

*Disabled by default (enable in entity settings if needed)

## Controls

### Switches

| Entity | Description | Default State |
|--------|-------------|---------------|
| Charging | Start/stop charging (reads actual charging state) | Off |
| Direct Mode | Plug-and-charge mode (auto-start when vehicle connected) | Unknown until set |
| Stop on Disconnect | Automatically stop session when vehicle disconnects | Unknown until set |

### Numbers (Sliders)

| Entity | Range | Step | Description | Default |
|--------|-------|------|-------------|---------|
| Max Charging Current | 6-32 A | 1 A | Maximum allowed charging current | Unknown until set |
| LED Brightness* | 0, 1, 3 | - | Screen/LED brightness (0=off, 1=low, 3=high) | Unknown until set |
| Max Voltage* | 265-290 V | 1 V | Maximum voltage protection threshold | Unknown until set |
| Min Voltage* | 70-110 V | 1 V | Minimum voltage protection threshold | Unknown until set |

*Disabled by default (enable in entity settings if needed)

### Buttons

| Entity | Action | Description |
|--------|--------|-------------|
| Reset Total Energy | Resets counter | Reset the total energy counter to zero |
| Start Charging* | Sends start command | Start charging (alternative to switch) |
| Stop Charging* | Sends stop command | Stop charging (alternative to switch) |

*Disabled by default (enable in entity settings if needed)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/americodias/duosida-ha`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Duosida" and install
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/duosida_ev` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Duosida"
4. Choose auto-discovery or manual configuration
5. If manual, enter your charger's IP address

## Requirements

- Duosida EV wall charger on your local network
- Network access to TCP port 9988 on the charger
- Home Assistant 2023.1 or newer

## Tested On

- Duosida SmartChargePI single-phase 7.2 kW

## Comparison with Cloud Integration

| Feature | This Integration | Cloud Integration |
|---------|-----------------|-------------------|
| Connection | Local TCP | Cloud API |
| Latency | Low (~10ms) | High (1-2s) |
| Internet Required | No | Yes |
| Privacy | Full control | Data in cloud |
| Reliability | High | Depends on cloud |

## Example Automations

### Solar-Powered Charging

Automatically adjust charging current based on solar production:

```yaml
automation:
  - alias: "EV - Adjust charging to solar production"
    trigger:
      - platform: state
        entity_id: sensor.solar_power
    condition:
      - condition: state
        entity_id: switch.duosida_ev_charger_charging
        state: "on"
    action:
      - service: number.set_value
        target:
          entity_id: number.duosida_ev_charger_max_charging_current
        data:
          value: >
            {% set solar = states('sensor.solar_power') | float(0) %}
            {% set current = (solar / 230) | round(0, 'floor') %}
            {{ [6, [current, 32] | min] | max }}
```

### Charge During Off-Peak Hours

Start charging automatically during cheap electricity hours:

```yaml
automation:
  - alias: "EV - Start charging at off-peak"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.car_connected
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.duosida_ev_charger_charging
      - service: number.set_value
        target:
          entity_id: number.duosida_ev_charger_max_charging_current
        data:
          value: 32

  - alias: "EV - Stop charging at peak hours"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.duosida_ev_charger_charging
```

### Temperature-Based Current Limiting

Reduce charging current if charger gets too hot:

```yaml
automation:
  - alias: "EV - Reduce current on high temperature"
    trigger:
      - platform: numeric_state
        entity_id: sensor.duosida_ev_charger_temperature
        above: 60
    action:
      - service: number.set_value
        target:
          entity_id: number.duosida_ev_charger_max_charging_current
        data:
          value: 16
      - service: notify.mobile_app
        data:
          title: "EV Charger Temperature Warning"
          message: "Charging current reduced due to high temperature"

  - alias: "EV - Restore current on normal temperature"
    trigger:
      - platform: numeric_state
        entity_id: sensor.duosida_ev_charger_temperature
        below: 50
    action:
      - service: number.set_value
        target:
          entity_id: number.duosida_ev_charger_max_charging_current
        data:
          value: 32
```

### Energy Dashboard Integration

The Total Energy sensor is automatically compatible with Home Assistant's Energy Dashboard. To add it:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption**
3. Select **Duosida EV Charger Total Energy**
4. Save

## FAQ

### Why do some settings show "Unknown"?

The integration uses an "unknown-first" approach. Settings like LED brightness, direct mode, and voltage thresholds cannot be read from the charger, so they start as "Unknown" until you explicitly set them. Once set, the values are stored and persist across Home Assistant restarts.

### What's the difference between Session Energy and Total Energy?

- **Session Energy**: Reported by the charger, resets when you start a new charging session
- **Total Energy**: Calculated by integrating power over time, never resets automatically (like an odometer)

Use Total Energy for the Energy Dashboard and lifetime tracking. Use Session Energy to see how much a single charge consumed.

### Why can't I set LED Brightness to 2?

The charger hardware only supports brightness values of 0 (off), 1 (low), and 3 (high). Value 2 is not accepted by the charger's firmware.

### How do I find my charger's IP address?

1. Use the auto-discovery feature when adding the integration
2. Check your router's DHCP client list for "SmartChargePI"
3. Use a network scanner app on your phone

Tip: Set a DHCP reservation in your router to keep the IP address stable.

### Does this work offline?

Yes! This integration communicates directly with your charger over your local network. No internet connection is required.

### Can I use this alongside the mobile app?

Yes, both can control the charger simultaneously. However, settings changed in the app won't be reflected in Home Assistant (since the charger doesn't report them back).

### What's "Direct Mode"?

Direct mode (also called plug-and-charge) automatically starts charging when you plug in your vehicle, without needing to start it manually via the app or Home Assistant.

### The charger supports Stop on Disconnect, but I can't see the current state?

Like other configuration settings, the charger doesn't report the current state. Once you set it via Home Assistant, the integration will remember and display the value you set.

## Troubleshooting

### Charger not discovered

**Symptoms:** Auto-discovery doesn't find your charger

**Solutions:**
- Ensure your charger and Home Assistant are on the same network (same subnet)
- Check that UDP ports 48890 and 48899 are not blocked by firewall
- Some routers block UDP broadcast - check router settings
- Try manual configuration with the charger's IP address instead
- Restart the charger and try discovery again

### Cannot connect to charger

**Symptoms:** "Failed to connect" error during setup

**Solutions:**
- Verify the charger is powered on and connected to network
- Check that TCP port 9988 is accessible from Home Assistant
- Try pinging the charger IP from Home Assistant host: `ping <charger_ip>`
- Check firewall rules on your network
- Verify the device ID is correct (19 digits starting with "03")
- Try restarting the charger by power cycling it

### Entities show "Unavailable"

**Symptoms:** All entities become unavailable

**Solutions:**
- Check the Home Assistant logs: **Settings** → **System** → **Logs**, filter for "duosida"
- Verify network connectivity to charger
- Check if charger is responding: `telnet <charger_ip> 9988`
- Restart the integration: **Settings** → **Devices & Services** → **Duosida** → **⋮** → **Reload**
- If problem persists, restart Home Assistant

### Values not updating

**Symptoms:** Sensor values frozen or not changing

**Solutions:**
- Check the scan interval setting (default is 10 seconds)
- Enable debug logging to see communication details:
  ```yaml
  logger:
    logs:
      custom_components.duosida_ev: debug
  ```
- Check Home Assistant logs for connection errors
- Verify charger is actually changing state (e.g., actually charging)
- Try reducing scan interval if network is slow

### Settings don't persist

**Symptoms:** LED brightness, direct mode, etc. reset after HA restart

**Solutions:**
- Check that `.storage/duosida_ev.*` file exists in your HA config directory
- Ensure Home Assistant has write permissions to the `.storage/` directory
- Check logs for storage-related errors
- Try setting the value again and verify it persists

### Integration won't load after update

**Symptoms:** Integration fails to load after updating

**Solutions:**
1. Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
2. Restart Home Assistant completely
3. Check logs for errors
4. Remove and re-add the integration if necessary (settings will be preserved if using same device ID)

### High temperature warnings

**Symptoms:** Temperature sensor shows >60°C

**Solutions:**
- Ensure adequate ventilation around the charger
- Check if charger is in direct sunlight
- Reduce max charging current temporarily
- Consider using the temperature-based automation example above
- If temperature exceeds 80°C, stop charging and contact support

### Debug logging

To enable detailed debug logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.duosida_ev: debug
    custom_components.duosida_ev.coordinator: debug
```

This will log all communication with the charger, helpful for troubleshooting connection issues.

### Getting help

If you can't resolve the issue:

1. Enable debug logging (see above)
2. Reproduce the problem
3. Check logs: **Settings** → **System** → **Logs**
4. Open an issue on [GitHub](https://github.com/americodias/duosida-ha/issues) with:
   - Home Assistant version
   - Integration version
   - Charger model
   - Relevant log entries
   - Steps to reproduce

## Credits

- Based on the [duosida-ev](https://github.com/americodias/duosida-ev) Python library
- Inspired by [jello1974/duosidaEV-home-assistant](https://github.com/jello1974/duosidaEV-home-assistant)

## License

MIT License - see [LICENSE](LICENSE) file
