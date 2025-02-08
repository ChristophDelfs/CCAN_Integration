"""CCAN Cover"""

from __future__ import annotations

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


class CCAN_Cover(CoverEntity):
    """Entity that controls a CCAN cover."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Create a CCAN cover device."""
        self.control_result: dict[str, Any] | None = None
        if self.coordinator.device.settings["rollers"][0]["positioning"]:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

    @property
    def is_closed(self) -> bool:
        """If cover is closed."""
        if self.control_result:
            return cast(bool, self.control_result["current_pos"] == 0)

        return cast(int, self.block.rollerPos) == 0

    @property
    def current_cover_position(self) -> int:
        """Position of the cover."""
        if self.control_result:
            return cast(int, self.control_result["current_pos"])

        return cast(int, self.block.rollerPos)

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        if self.control_result:
            return cast(bool, self.control_result["state"] == "close")

        return self.block.roller == "close"

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        if self.control_result:
            return cast(bool, self.control_result["state"] == "open")

        return self.block.roller == "open"

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        self.control_result = await self.set_state(go="close")
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover."""
        self.control_result = await self.set_state(go="open")
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        self.control_result = await self.set_state(
            go="to_pos", roller_pos=kwargs[ATTR_POSITION]
        )
        self.async_write_ha_state()

    async def async_stop_cover(self, **_kwargs: Any) -> None:
        """Stop the cover."""
        self.control_result = await self.set_state(go="stop")
        self.async_write_ha_state()

    @callback
    def _update_callback(self) -> None:
        """When device updates, clear control result that overrides state."""
        self.control_result = None
        super()._update_callback()


class RpcShellyCover(ShellyRpcEntity, CoverEntity):
    """Entity that controls a cover on RPC based Shelly devices."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator: ShellyRpcCoordinator, id_: int) -> None:
        """Initialize rpc cover."""
        super().__init__(coordinator, f"cover:{id_}")
        self._id = id_
        if self.status["pos_control"]:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION
        if coordinator.device.config[f"cover:{id_}"].get("slat", {}).get("enable"):
            self._attr_supported_features |= (
                CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.STOP_TILT
                | CoverEntityFeature.SET_TILT_POSITION
            )

    @property
    def is_closed(self) -> bool | None:
        """If cover is closed."""
        return cast(bool, self.status["state"] == "closed")

    @property
    def current_cover_position(self) -> int | None:
        """Position of the cover."""
        if not self.status["pos_control"]:
            return None

        return cast(int, self.status["current_pos"])

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Return current position of cover tilt."""
        if "slat_pos" not in self.status:
            return None

        return cast(int, self.status["slat_pos"])

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return cast(bool, self.status["state"] == "closing")

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return cast(bool, self.status["state"] == "opening")

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self.call_rpc("Cover.Close", {"id": self._id})

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open cover."""
        await self.call_rpc("Cover.Open", {"id": self._id})

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        await self.call_rpc(
            "Cover.GoToPosition", {"id": self._id, "pos": kwargs[ATTR_POSITION]}
        )

    async def async_stop_cover(self, **_kwargs: Any) -> None:
        """Stop the cover."""
        await self.call_rpc("Cover.Stop", {"id": self._id})

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        await self.call_rpc("Cover.GoToPosition", {"id": self._id, "slat_pos": 100})

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        await self.call_rpc("Cover.GoToPosition", {"id": self._id, "slat_pos": 0})

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        await self.call_rpc(
            "Cover.GoToPosition",
            {"id": self._id, "slat_pos": kwargs[ATTR_TILT_POSITION]},
        )

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.call_rpc("Cover.Stop", {"id": self._id})
