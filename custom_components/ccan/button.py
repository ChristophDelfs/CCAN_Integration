"""Button for CCAN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast
import logging

from homeassistant.components.button import (
    # DOMAIN as BINARY_SENSOR_PLATFORM,
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
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
class CCAN_Button_Description:
    manufacturer: str
    device_class: ButtonDeviceClass
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

    buttons: list[CCAN_Button] = [
        CCAN_Button(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_BUTTON")
    ]

    if len(buttons) > 0:
        coordinator.initialize_count += 1

    async_add_entities(buttons)
    _LOGGER.info("Added %d buttons", len(buttons))


class CCAN_Button(ButtonEntity):
    """Represent a block binary sensor entity."""

    def __init__(
        self,
        coordinator: CCAN_Coordinator,
        device: ResolvedHomeAssistantDeviceInstance,
    ) -> None:
        """Create a CCAN Reed Contect device."""
        self.coordinator = coordinator
        self.ha_library = coordinator.ha_library
        self.device = device
        _attr_device_class = ButtonDeviceClass

        self._closed = None

        self._name = self.ha_library.get_device_parameter_value(device, "name")

        events = self.ha_library.get_symbolic_event(self.device, "PRESSED")
        for event in events:
            self.coordinator.add_listening_event(event, self.press)

        self.coordinator.register_entity(self)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self._name,
            manufacturer="",
            model="Reedkontakt",
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

    def get_variables(self):
        return []

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return self._name
