"""Binary sensor for CCAN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast
import logging

from homeassistant.components.binary_sensor import (
    # DOMAIN as BINARY_SENSOR_PLATFORM,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

from homeassistant.helpers.device_registry import DeviceInfo
from .coordinator import CCAN_Coordinator
from homeassistant.config_entries import ConfigEntry

from .api.base.PlatformDefaults import PlatformDefaults
from .api.resolver.ResolverElements import ResolvedHomeAssistantDeviceInstance


@dataclass
class CCAN_BinarySensor_Description:
    manufacturer: str
    device_class: BinarySensorDeviceClass
    entity_category: EntityCategory
    quantity_on_hand: int = 0


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all climate."""
    coordinator: CCAN_Coordinator = hass.data[DOMAIN][config_entry.entry_id].coordinator

    window_sensors: list[CCAN_WindowSensor] = [
        CCAN_WindowSensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_BINARY_SENSOR_WINDOW")
    ]

    door_sensors: list[CCAN_DoorSensor] = [
        CCAN_DoorSensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_BINARY_SENSOR_DOOR")
    ]

    motion_sensors: list[CCAN_MotionSensor] = [
        CCAN_MotionSensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_BINARY_SENSOR_MOTION")
    ]

    button_sensors: list[CCAN_ButtonSensor] = [
        CCAN_ButtonSensor(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_BINARY_SENSOR_BUTTON")
    ]

    if len(window_sensors) > 0:
        coordinator.initialize_count += 1

    if len(door_sensors) > 0:
        coordinator.initialize_count += 1

    if len(motion_sensors) > 0:
        coordinator.initialize_count += 1

    if len(button_sensors) > 0:
        coordinator.initialize_count += 1

    # Add Lights to HA:
    async_add_entities(window_sensors)
    _LOGGER.info("Added %d window sensors", len(window_sensors))

    async_add_entities(door_sensors)
    _LOGGER.info("Added %d door sensors", len(door_sensors))

    async_add_entities(motion_sensors)
    _LOGGER.info("Added %d motion sensors", len(motion_sensors))

    async_add_entities(button_sensors)
    _LOGGER.info("Added %d button sensors", len(button_sensors))


class CCAN_BinarySensorEntity(BinarySensorEntity):
    """Represent a block binary sensor entity."""

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Create a CCAN Reed Contect device."""
        self.coordinator = coordinator
        self.ha_library = coordinator.ha_library
        self.device = device

        self._name = self.ha_library.get_device_parameter_value(device, "name")

        self._state = None
        self.add_listeners()
        self.coordinator.register_entity(self)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self._name,
            manufacturer="",
            model="Binärsensor",
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

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.device.get_name()}"

    @property
    def available(self) -> bool:
        """Return the availability of the entity."""
        return self._state is not None

    @property
    def is_on(self) -> bool:
        """Return true if sensor state is on."""
        return not self._state

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return self._name

    def set_state(self, value) -> None:
        self._state = value
        print(f"Binary Sensor  {self._name} : {self._state}")
        self.schedule_update_ha_state()

    def set_state_on(self, **kwargs: Any) -> None:
        self.set_state(True)

    def set_state_off(self, **kwargs: Any) -> None:
        self.set_state(False)


class CCAN_WindowSensor(CCAN_BinarySensorEntity):
    """Represent a window binary sensor entity."""

    _attr_device_class = BinarySensorDeviceClass.WINDOW

    def add_listeners(self):
        events = self.ha_library.get_symbolic_event(self.device, "OPEN")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_state_off)

        events = self.ha_library.get_symbolic_event(self.device, "CLOSED")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_state_on,
            )

    def get_variables(self):
        return [("STATUS", self.set_state)]


class CCAN_DoorSensor(CCAN_BinarySensorEntity):
    """Represent a door binary sensor entity."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def add_listeners(self):
        events = self.ha_library.get_symbolic_event(self.device, "OPEN")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_state_off)

        events = self.ha_library.get_symbolic_event(self.device, "CLOSED")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_state_on,
            )

    def get_variables(self):
        return [("STATUS", self.set_state)]


class CCAN_MotionSensor(CCAN_BinarySensorEntity):
    """Represent a block binary sensor entity."""

    _attr_device_class = BinarySensorDeviceClass.MOTION

    def add_listeners(self):
        events = self.ha_library.get_symbolic_event(self.device, "NEW_MOTION_DETECTED")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_state_on)

        events = self.ha_library.get_symbolic_event(self.device, "MOTION_COMPLETED")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_state_off,
            )

    def get_variables(self):
        return [("MOTION_ACTIVE", self.set_state)]


class CCAN_ButtonSensor(CCAN_BinarySensorEntity):
    """Represent a block binary sensor entity."""

    _attr_device_class = None  # BinarySensorDeviceClass

    def add_listeners(self):
        events = self.ha_library.get_symbolic_event(self.device, "PRESSED")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_state_on)

        events = self.ha_library.get_symbolic_event(self.device, "RELEASED")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_state_off)

    def get_variables(self):
        return [("STATE", self.set_state)]
