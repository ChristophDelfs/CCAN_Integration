from __future__ import annotations

"""Platform for light integration."""


import logging
import random

import asyncio

# import awesomelights
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity, ColorMode

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .coordinator import CCAN_Coordinator
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN


from .api.resolver.ResolverElements import ResolvedHomeAssistantDeviceInstance


_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        #  vol.Required(CONF_HOST): cv.string,
        #  vol.Optional(CONF_USERNAME, default="admin"): cv.string,
        #  vol.Optional(CONF_PASSWORD): cv.string,
    }
)

# Coordinator: ExampleCoordinator = None


# def setup_platform(
#    hass: HomeAssistant,
#    config: ConfigType,
#    add_entities: AddEntitiesCallback,
#    discovery_info: DiscoveryInfoType | None = None,
# ) -> None:
#    """Set up the Awesome Light platform."""
#    pass
# Assign configuration variables.
# The configuration check takes care they are present.
# host = config[CONF_HOST]
# username = config[CONF_USERNAME]
# password = config.get(CONF_PASSWORD)

# Setup connection with devices/cloud
# hub = awesomelights.Hub(host, username, password)

# Verify that passed in configuration works
# if not hub.is_valid_login():
#    _LOGGER.error("Could not connect to AwesomeLight hub")
#    return

# Add devices
# add_entities(AwesomeLight(light) for light in hub.lights())


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Lights."""
    coordinator: CCAN_Coordinator = hass.data[DOMAIN][config_entry.entry_id].coordinator

    lights: list[CCAN_Light] = [
        CCAN_Light(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_LIGHT")
    ]

    if len(lights) > 0:
        coordinator.initialize_count += 1

    # Add Lights to HA:
    async_add_entities(lights)
    _LOGGER.info("Added %d lights", len(lights))


class CCAN_Light(CoordinatorEntity, LightEntity):
    """Representation of an Awesome Light."""

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ):
        super().__init__(coordinator)
        """Initialize an AwesomeLight."""
        # self._light = light

        self.coordinator = coordinator
        self.ha_library = coordinator.ha_library
        self.device = device

        self._name = self.ha_library.get_device_parameter_value(device, "name")
        self._brightness = None
        self._state = None

        events = self.ha_library.get_symbolic_event(self.device, "ON")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.external_update_on,
            )

        events = self.ha_library.get_symbolic_event(self.device, "OFF")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.external_update_off,
            )

        self.coordinator.register_entity(self)

    @property
    def initialized(self):
        return self._state is not None

    @property
    def color_mode(self):
        return ColorMode.UNKNOWN

    @property
    def supported_color_modes(self):
        return [ColorMode.ONOFF]

    @property
    def device_class(self) -> str:
        """Return device class."""
        # https://developers.home-assistant.io/docs/core/entity/binary-sensor#available-device-classes
        return BinarySensorDeviceClass.LIGHT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            name=self._name,
            manufacturer="",
            model="Lampe",
            sw_version="1.0",
            identifiers={
                (
                    DOMAIN,
                    f"{self.device.get_name()}",
                )
            },
            suggested_area=self.ha_library.get_device_parameter_value(
                self.device, "suggested_area"
            ),
        )

    # @property
    # def should_polling(self):
    #    return False

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    # @property
    # def brightness(self):
    #    """Return the brightness of the light.
    #
    #    This method is optional. Removing it indicates to Home Assistant
    #    that brightness is not supported for this light.
    #    """
    #    return self._brightness

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.device.get_name()}"

    def get_variables(self):
        return [("STATUS", self.update)]

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""

        return self._state if self._state is not None else False

    def turn_on(self) -> None:
        """Instruct the light to turn on. This method does not change the state itself. This is done after receiving an update from the CCAN network."""

        events = self.ha_library.get_symbolic_event(self.device, "TURN_ON")
        for event in events:
            self.coordinator.connector.send_event(event)

    def turn_off(self) -> None:
        """Instruct the light to turn off. This method does not change the state itself. This is done after receiving an update from the CCAN network."""

        events = self.ha_library.get_symbolic_event(self.device, "TURN_OFF")
        for event in events:
            self.coordinator.connector.send_event(event)

    def external_update_on(self, *args) -> None:
        self.update(True)

    def external_update_off(self, *args) -> None:
        self.update(False)

    def update(self, new_value) -> None:
        self._state = new_value
        # self._state = False if self._state else True
        self.schedule_update_ha_state()

    # https://developers.home-assistant.io/docs/core/entity
