"""Sensors for CCAN"""

from __future__ import annotations
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)


from homeassistant.helpers.device_registry import DeviceInfo

from homeassistant.const import DEGREE, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass

from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_PICTURE_TEMPLATE,
    CONF_ICON_TEMPLATE,
    CONF_NAME,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)


from .const import DOMAIN
from .coordinator import CCAN_Coordinator
from .const import DOMAIN


from .api.resolver.ResolverElements import ResolvedHomeAssistantDeviceInstance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors"""
    coordinator: CCAN_Coordinator = hass.data[DOMAIN][config_entry.entry_id].coordinator

    sensors: list[CCAN_Sensor] = [
        CCAN_Sensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_TEMPERATURE_SENSOR")
    ]

    if len(sensors) > 0:
        coordinator.initialize_count += 1

    # Add Sensors to HA:
    async_add_entities(sensors)
    _LOGGER.info("Added %d sensors", len(sensors))


class CCAN_Sensor(CoordinatorEntity, SensorEntity):
    """CCAN sensor entity."""

    _attr_native_unit_of_measurement = (UnitOfTemperature.CELSIUS,)
    _attr_device_class = (SensorDeviceClass.TEMPERATURE,)
    _attr_state_class = (SensorStateClass.MEASUREMENT,)

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.ha_library = coordinator.ha_library
        self.device = device
        self._temperature = None

        self._name = self.ha_library.get_device_parameter_value(device, "name")

        events = self.ha_library.get_symbolic_event(self.device, "CURRENT_TEMPERATURE")
        for event in events:
            self.coordinator.add_listening_event(event, self.update)

        self.coordinator.register_entity(self)

    def update(self, value):
        if value > -100 and value < 100:
            self._temperature = value
            print("new temperature received:", value)
            self.schedule_update_ha_state()

    def get_variables(self):
        return [("TEMPERATURE", self.update)]

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.device.get_name()}"

    @property
    def name(self):
        return self._name

    @property
    def initialized(self):
        return self._temperature is not None

    @property
    def available(self):
        return self._temperature is not None

    @property
    def native_value(self) -> int | float:
        """Return the state of the entity."""
        # Using native value and native unit of measurement, allows you to change units
        # in Lovelace and HA will automatically calculate the correct value.
        return self._temperature

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            name=self._name,
            manufacturer="Dallas",
            model="DS18B20",
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
