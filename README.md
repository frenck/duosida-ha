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

| Sensor | Description |
|--------|-------------|
| Status | Current charger state (Available, Charging, etc.) |
| CP State | Control Pilot state |
| Voltage | Line voltage (V) |
| Current | Charging current (A) |
| Power | Power consumption (W) |
| Temperature | Charger temperature (°C) |
| Session Energy | Energy used in current session (kWh) |
| Session Time | Duration of current session (min) |
| Max Current Setting | Current max current setting (A) |

## Controls

- **Charging Switch**: Start/stop charging
- **Direct Mode Switch**: Enable/disable plug-and-charge mode
- **Stop Session on Vehicle Disconnect Switch**: Auto-stop when vehicle disconnects
- **Max Current Slider**: Set maximum charging current (6-32A)
- **LED Brightness Slider**: Set LED/screen brightness
- **Start/Stop Buttons**: Alternative charging control

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

1. Copy the `custom_components/duosida_local` folder to your Home Assistant's `custom_components` directory
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

## Troubleshooting

### Charger not discovered

- Ensure your charger and Home Assistant are on the same network
- Check that UDP port 48890/48899 is not blocked
- Try manual configuration with the charger's IP address

### Cannot connect

- Verify TCP port 9988 is accessible
- Check if the charger is powered on and connected to the network
- Try restarting the charger

### Values not updating

- Increase the scan interval in the integration options
- Check the Home Assistant logs for errors

## Credits

- Based on the [duosida-ev](https://github.com/americodias/duosida-ev) Python library
- Inspired by [jello1974/duosidaEV-home-assistant](https://github.com/jello1974/duosidaEV-home-assistant)

## License

MIT License - see [LICENSE](LICENSE) file
