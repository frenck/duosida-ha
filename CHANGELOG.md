# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-21

### Added

- **Local Control**: Direct TCP communication with Duosida EV wall chargers (port 9988), no cloud dependency
- **28 Entities**:
  - 17 sensors (status, voltage, current, power, temperature, energy, etc.)
  - 1 binary sensor (charging status)
  - 3 switches (charging, direct mode, stop on disconnect)
  - 4 number controls (max current, LED brightness, voltage thresholds)
  - 3 buttons (start charging, stop charging, reset total energy)
- **Settings Persistence**: Unknown-first approach - settings persist across restarts without assuming defaults
- **Total Energy Integration**: Calculates lifetime energy consumption using trapezoidal integration
- **Auto-Recovery**: Exponential backoff for connection failures
- **Charging Switch Debounce**: Configurable debounce (5-120s) prevents UI bounce during state transitions
- **Options Flow**: Reconfigure scan interval and switch debounce without removing the integration
- **Config Flow**: Setup wizard with automatic device discovery
- **20 Language Translations**: Full localization support
- **Home Assistant Energy Dashboard**: Compatible total energy sensor

### Technical

- 68 tests with 96% code coverage
- Strict typing with mypy
- Code quality with ruff and black
- Uses `duosida-ev` library (v0.1.3) for charger communication

[1.0.0]: https://github.com/americodias/duosida-ha/releases/tag/v1.0.0
