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
    UnitOfElectricPotential,
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

    temperature_sensors: list[CCAN_Temperature_Sensor] = [
        CCAN_Temperature_Sensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_TEMPERATURE_SENSOR")
    ]

    if len(temperature_sensors) > 0:
        coordinator.initialize_count += 1

        # Add Sensors to HA:
        async_add_entities(temperature_sensors)
        _LOGGER.info("Added %d temperature sensors", len(temperature_sensors))

    voltage_sensors: list[CCAN_Voltage_Sensor] = [
        CCAN_Voltage_Sensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_VOLTAGE_SENSOR")
    ]

    if len(voltage_sensors) > 0:
        coordinator.initialize_count += 1

        # Add Sensors to HA:
        async_add_entities(voltage_sensors)
        _LOGGER.info("Added %d voltage sensors", len(voltage_sensors))


class CCAN_Sensor(CoordinatorEntity, SensorEntity):
    """CCAN sensor entity."""

    _attr_state_class = (SensorStateClass.MEASUREMENT,)

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.ha_library = coordinator.ha_library
        self.device = device
        self._value = None
        self._model = "unknown model"
        self._manufacturer = "unknown manufacturer"
        self._name = self.ha_library.get_device_parameter_value(device, "name")
        self._location = self.ha_library.get_device_parameter_value(
            self.device, "suggested_area"
        )
        self._entity_id = coordinator.create_entity_name(
            "sensor", self._location, self._name
        )

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.device.get_name()}"

    @property
    def entity_id(self) -> str:
        """Return the display name of this light."""
        return self._entity_id

    @entity_id.setter
    def entity_id(self, new_entity_id):
        self._entity_id = new_entity_id

    @property
    def name(self):
        return self._name

    @property
    def initialized(self):
        return self._value is not None

    @property
    def available(self):
        return self._value is not None

    @property
    def native_value(self) -> int | float:
        """Return the state of the entity."""
        # Using native value and native unit of measurement, allows you to change units
        # in Lovelace and HA will automatically calculate the correct value.
        return self._value

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            name=self._name,
            manufacturer=self._manufacturer,
            model=self._model,
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


class CCAN_Temperature_Sensor(CCAN_Sensor):
    """CCAN sensor entity."""

    _attr_native_unit_of_measurement = (UnitOfTemperature.CELSIUS,)
    _attr_device_class = (SensorDeviceClass.TEMPERATURE,)

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device)

        self._location = self.ha_library.get_device_parameter_value(
            self.device, "suggested_area"
        )
        self._entity_id = coordinator.create_entity_name(
            "sensor", self._location, self._name
        )

        events = self.ha_library.get_symbolic_event(self.device, "CURRENT_TEMPERATURE")
        for event in events:
            self.coordinator.add_listening_event(event, self.update)

        self.coordinator.register_entity(self)

    def update(self, value):
        if value > -100 and value < 100:
            self._value = value
            print("new temperature received:", value)
            self.schedule_update_ha_state()

    def get_variables(self):
        return [("TEMPERATURE", self.update)]


class CCAN_Voltage_Sensor(CCAN_Sensor):
    """CCAN sensor entity."""

    _attr_native_unit_of_measurement = (UnitOfElectricPotential.VOLT,)
    _attr_device_class = (SensorDeviceClass.VOLTAGE,)

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device)

        events = self.ha_library.get_symbolic_event(self.device, "CURRENT_VOLTAGE")
        for event in events:
            self.coordinator.add_listening_event(event, self.update)

        self.coordinator.register_entity(self)

    def update(self, value):
        if value > -100 and value < 100:
            self._value = value
            print("new voltage received:", value)
            self.schedule_update_ha_state()

    def get_variables(self):
        return [("VOLTAGE", self.update)]
