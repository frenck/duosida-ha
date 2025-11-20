"""
Config flow for Duosida Local integration.

The config flow handles the setup wizard when a user adds the integration.
It guides the user through:
1. Choosing between auto-discovery or manual configuration
2. Selecting a discovered device or entering details manually
3. Testing the connection
4. Saving the configuration

Home Assistant automatically shows this flow when the user clicks
"Add Integration" and selects "Duosida EV Charger (Local)".
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import AbortFlow, FlowResult

from duosida_ev import DuosidaCharger, discover_chargers

from .const import (
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DuosidaLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """
    Handle a config flow for Duosida Local.

    The domain=DOMAIN parameter links this flow to our integration.
    Home Assistant uses this to know which flow to show.
    """

    # Schema version - increment if you change the config structure
    # This allows Home Assistant to migrate old configs
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        # Store discovered devices between steps
        self._discovered_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the initial step.

        This is called when the user first opens the config flow.
        We ask if they want to auto-discover or configure manually.

        Args:
            user_input: Form data if user submitted, None on first display

        Returns:
            FlowResult: Either show form or proceed to next step
        """
        if user_input is not None:
            # User submitted the form
            if user_input.get("discovery"):
                # User chose auto-discovery
                return await self.async_step_discovery()
            # User chose manual configuration
            return await self.async_step_manual()

        # Show the initial form
        # vol.Schema defines the form fields
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    # Checkbox for choosing discovery mode
                    vol.Required("discovery", default=True): bool,
                }
            ),
            description_placeholders={
                "discovery_description": "Auto-discover chargers on the network"
            },
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the discovery step.

        This step:
        1. Scans the network for Duosida chargers
        2. Shows a list of found devices
        3. Lets the user select one

        Args:
            user_input: Selected device if user submitted

        Returns:
            FlowResult: Show device list or create config entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # User selected a device from the list
            selected = user_input["device"]

            # Find the full device info
            for device in self._discovered_devices:
                if device["ip"] == selected:
                    # Check if this device is already configured
                    await self.async_set_unique_id(device["device_id"])
                    self._abort_if_unique_id_configured()

                    # Create the config entry
                    # This saves the configuration and finishes the flow
                    return self.async_create_entry(
                        title=f"Duosida {device['ip']}",
                        data={
                            CONF_HOST: device["ip"],
                            CONF_PORT: DEFAULT_PORT,
                            CONF_DEVICE_ID: device["device_id"],
                            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        },
                    )

        # Discover devices on the network
        # async_add_executor_job runs the blocking discovery in a thread
        _LOGGER.debug("Starting device discovery")
        self._discovered_devices = await self.hass.async_add_executor_job(
            discover_chargers, 5  # 5 second timeout
        )
        _LOGGER.debug("Found %d devices", len(self._discovered_devices))

        if not self._discovered_devices:
            # No devices found - show error
            return self.async_show_form(
                step_id="discovery",
                errors={"base": "no_devices_found"},
            )

        # Build a dictionary for the dropdown
        # Key is the IP (used as value), value is the display text
        devices = {
            device["ip"]: f"{device['ip']} ({device.get('device_id', 'Unknown')})"
            for device in self._discovered_devices
        }

        # Show the device selection form
        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema(
                {
                    # Dropdown menu of discovered devices
                    vol.Required("device"): vol.In(devices),
                }
            ),
            errors=errors,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle manual configuration step.

        This step lets the user enter:
        - IP address (required)
        - Port (optional, defaults to 9988)
        - Device ID (optional, will be retrieved automatically)
        - Scan interval (optional)

        We test the connection before saving.

        Args:
            user_input: Form data if user submitted

        Returns:
            FlowResult: Show form or create config entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Extract form values
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            device_id = user_input.get(CONF_DEVICE_ID)

            # Test the connection
            try:
                _LOGGER.debug("Testing connection to %s:%s", host, port)

                # Create a charger instance
                # Using lambda because DuosidaCharger.__init__ can't be awaited directly
                charger = await self.hass.async_add_executor_job(
                    lambda: DuosidaCharger(
                        host=host,
                        port=port,
                        device_id=device_id or "test",  # Temporary ID for testing
                        debug=False,
                    )
                )

                # Try to connect
                connected = await self.hass.async_add_executor_job(charger.connect)

                if not connected:
                    errors["base"] = "cannot_connect"
                else:
                    # Connection successful
                    # Get device ID if not provided
                    if not device_id:
                        status = await self.hass.async_add_executor_job(
                            charger.get_status
                        )
                        if status:
                            # The charger object stores the device ID after connection
                            device_id = charger.device_id
                            _LOGGER.debug("Retrieved device ID: %s", device_id)
                        else:
                            errors["base"] = "cannot_connect"

                    # Clean up the test connection
                    await self.hass.async_add_executor_job(charger.disconnect)

                    if not errors:
                        # Check if this device is already configured
                        await self.async_set_unique_id(device_id)
                        self._abort_if_unique_id_configured()

                        # All good - create the config entry
                        return self.async_create_entry(
                            title=f"Duosida {host}",
                            data={
                                CONF_HOST: host,
                                CONF_PORT: port,
                                CONF_DEVICE_ID: device_id,
                                CONF_SCAN_INTERVAL: user_input.get(
                                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                                ),
                            },
                        )

            except AbortFlow:
                # Re-raise abort flow to let it complete the abort
                raise
            except Exception as e:
                _LOGGER.error("Error connecting to charger: %s", e)
                errors["base"] = "cannot_connect"

        # Show the manual configuration form
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    # Required: IP address
                    vol.Required(CONF_HOST): str,
                    # Optional: Port with default
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    # Optional: Device ID (will be auto-detected)
                    vol.Optional(CONF_DEVICE_ID): str,
                    # Optional: Update interval with default
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            ),
            errors=errors,
        )
