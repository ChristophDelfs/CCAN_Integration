"""CCAN Cover"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, cast
import logging

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CCAN_Coordinator
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from homeassistant.helpers.device_registry import DeviceInfo

from .api.base.PlatformDefaults import PlatformDefaults
from .api.resolver.ResolverElements import ResolvedHomeAssistantDeviceInstance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all climate."""
    coordinator: CCAN_Coordinator = hass.data[DOMAIN][config_entry.entry_id].coordinator

    covers: list[CCAN_Cover] = [
        CCAN_Cover(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_COVER")
    ]

    if len(covers) > 0:
        coordinator.initialize_count += 1

    # Add Lights to HA:
    async_add_entities(covers)
    _LOGGER.info("Added %d covers", len(covers))


class CoverState(Enum):
    CLOSING = 0
    CLOSED = 1
    OPENING = 2
    OPEN = 3
    STOPPED = 4
    UNKNOWN = 5


class CCAN_Cover(CoverEntity):
    """Entity that controls a CCAN cover."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Create a CCAN cover device."""
       
        self._cover_state = CoverState.UNKNOWN
        self._position = None
        self.coordinator = coordinator
        self.ha_library = coordinator.ha_library
        self.device = device

        self._name = self.ha_library.get_device_parameter_value(device, "name")

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "OPENING"), self.set_opening
        )

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "CLOSING"), self.set_closing
        )

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "OPENING_DONE"),
            self.set_open,
        )

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "CLOSING_DONE"),
            self.set_closed,
        )

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "STOPPED"), self.set_stopped
        )

        self.coordinator.add_listening_events(
            self.ha_library.get_symbolic_event(self.device, "CURRENT_POSITION"),
            self.set_cover_position,
        )
        self.coordinator.register_entity(self)

    def get_variables(self):
        return [("POSITION", self.set_initial_cover_position)]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            name=self._name,
            manufacturer="",
            model="Rolladen",
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
    def name(self):
        return self._name

    @property
    def available(self) -> bool:
        return self._cover_state != CoverState.UNKNOWN

    @property
    def is_closed(self) -> bool:
        """If cover is closed."""
        return self._cover_state == CoverState.CLOSED

    @property
    def current_cover_position(self) -> int:
        """Position of the cover."""
        if self._position is not None:
            return self._position
        return None

    def set_initial_cover_position(self, value):
        if 0 < value < 100:
            self._position = value
        if value == 100:
            self._cover_state = CoverState.OPEN
        elif value == 0:
            self._cover_state = CoverState.CLOSED
        else:
            self._cover_state = CoverState.STOPPED
        self.schedule_update_ha_state()

    def set_cover_position(self, value):
        self._position = 100 - int(value)

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return self._cover_state == CoverState.CLOSING

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return self._cover_state == CoverState.OPENING

    @property
    def is_open(self) -> bool:
        """Return if the cover is opening."""
        return self._cover_state == CoverState.OPEN

    @property
    def is_closed(self) -> bool:
        """Return if the cover is opening."""
        return self._cover_state == CoverState.CLOSED

    @property
    def is_stopped(self) -> bool:
        """Return if the cover is stopped."""
        return self._cover_state == CoverState.STOPPED

    def set_open(self, **kwargs: Any):
        self.state_update(CoverState.OPEN)

    def set_opening(self, **kwargs: Any):
        self.state_update(CoverState.OPENING)

    def set_closing(self, **kwargs: Any) -> bool:
        self.state_update(CoverState.CLOSING)

    def set_closed(self, **kwargs: Any):
        self.state_update(CoverState.CLOSED)

    def set_stopped(self, **kwargs: Any):
        self.state_update(CoverState.STOPPED)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        if (
            not self.is_stopped and not self.is_open
        ) or self._cover_state == CoverState.UNKNOWN:
            await asyncio.to_thread(self.ha_library.send, self.device, "STOP")
            while not self.is_stopped:
                await asyncio.sleep(0.1)
        await asyncio.to_thread(self.ha_library.send, self.device, "CLOSE")
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover."""

        if (
            not self.is_stopped and not self.is_closed
        ) or self._cover_state == CoverState.UNKNOWN:
            await asyncio.to_thread(self.ha_library.send, self.device, "STOP")
            while not self.is_stopped:
                await asyncio.sleep(0.1)
        await asyncio.to_thread(self.ha_library.send, self.device, "OPEN")
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if (position := kwargs.get(ATTR_POSITION)) is not None:
            await asyncio.to_thread(
                self.ha_library.send, self.device, "SET_POSITION", 100-position
            )
        self.async_write_ha_state()

    async def async_stop_cover(self, **_kwargs: Any) -> None:
        """Stop the cover."""

        await asyncio.to_thread(self.ha_library.send, self.device, "STOP")
        self.async_write_ha_state()

    def state_update(self, new_state) -> None:
        """When device updates, clear control result that overrides state."""
        self._cover_state = new_state
        self.schedule_update_ha_state()
