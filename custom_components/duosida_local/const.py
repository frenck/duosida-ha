"""
Constants for the Duosida Local integration.

This file contains all the constant values used throughout the integration.
Keeping constants in one place makes them easy to find and update.

Types used:
- Final: Indicates the value should never be changed
"""
from typing import Final

# =============================================================================
# Integration identifiers
# =============================================================================

# Domain is the unique identifier for this integration
# Used in hass.data, entity unique IDs, etc.
# Must match the folder name and manifest.json domain
DOMAIN: Final = "duosida_local"

# Human-readable name shown in the UI
NAME: Final = "Duosida EV Charger"

# Key used to store the coordinator in hass.data
COORDINATOR: Final = "coordinator"

# =============================================================================
# Configuration keys
# =============================================================================

# Keys used in config entry data
# These match the keys used in the config flow
CONF_DEVICE_ID: Final = "device_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# =============================================================================
# Default values
# =============================================================================

# Default TCP port for Duosida chargers
DEFAULT_PORT: Final = 9988

# Default polling interval in seconds
# How often we fetch status from the charger
DEFAULT_SCAN_INTERVAL: Final = 10

# =============================================================================
# Status codes
# =============================================================================

# Charger connection status codes
# These come from the conn_status field in charger status
# Source: Official Duosida Home Assistant integration
STATUS_CODES: Final = {
    0: "Available",     # Charger is ready, no vehicle connected
    1: "Preparing",     # Vehicle connected, preparing to charge
    2: "Charging",      # Actively charging
    3: "Cooling",       # Cooling down after charging
    4: "SuspendedEV",   # Charging suspended by vehicle
    5: "Finished",      # Charging complete
    6: "Holiday",       # Holiday mode (scheduled off)
}

