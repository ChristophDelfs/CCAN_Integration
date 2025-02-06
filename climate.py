"""Climate device for CCM15 coordinator."""

import logging
from typing import Any
import asyncio

# from ccm15 import CCM15DeviceState

from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    UnitOfTemperature,
)


from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_ON,
    SWING_OFF,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorDeviceClass
# from .api import Device, DeviceType

from .const import CONST_CMD_FAN_MAP, CONST_CMD_STATE_MAP, DOMAIN

from .coordinator import CCAN_Coordinator
from homeassistant.config_entries import ConfigEntry


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

    climates: list[CCAN_Climate] = [
        CCAN_Climate(coordinator, device)
        for device in coordinator.ha_library.get_devices("HA_CLIMATE")
    ]

    if len(climates) > 0:
        coordinator.initialize_count += 1

    # Add Lights to HA:
    async_add_entities(climates)
    _LOGGER.info("Added %d heatings", len(climates))


class CCAN_Climate(ClimateEntity):
    """Climate device for CCAN based heating."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True
    _attr_target_temperature_step = PRECISION_HALVES
    _attr_hvac_modes = [
        HVACMode.OFF,
        # HVACMode.HEAT,
        #  HVACMode.COOL,
        # HVACMode.DRY,
        # HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_ON]
    _attr_supported_features = (
        #
        #
        # | ClimateEntityFeature.FAN_MODE
        # | ClimateEntityFeature.SWING_MODE
        ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TARGET_TEMPERATURE
        # | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    )

    _attr_target_temperature_low: float | None = None
    _attr_target_temperature_high: float | None = None
    _attr_name = None
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self, coordinator: CCAN_Coordinator, device: ResolvedHomeAssistantDeviceInstance
    ) -> None:
        """Create a CCAN climate device."""

        self.coordinator = coordinator
        self.ha_library = coordinator.ha_library
        self.device = device

        self._name = self.ha_library.get_device_parameter_value(device, "name")

        # internal states:
        self._heating_control_on = None
        self._heating_is_active = None
        self._enabled = None

        self._target_temperature = None
        self._current_temperature = None

        self._attr_unique_id = "378102xX"

        # self._attr_target_temperature_low = 18
        # self._attr_target_temperature_high = 25

        self._hvac_mode = None

        events = self.ha_library.get_symbolic_event(self.device, "ON")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_heating_state_on,
            )

        events = self.ha_library.get_symbolic_event(self.device, "OFF")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_heating_state_off,
            )

        events = self.ha_library.get_symbolic_event(self.device, "ACTIVE")
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_heating_is_active,
            )

        events = self.ha_library.get_symbolic_event(self.device, "PASSIVE")
        for event in events:
            self.coordinator.add_listening_event(event, self.set_heating_is_passive)

        events = self.ha_library.get_symbolic_event(
            self.device, "CURRENT_TEMPERATURE_CHANGED"
        )
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_current_temperature,
            )

        events = self.ha_library.get_symbolic_event(
            self.device, "TARGET_TEMPERATURE_CHANGED"
        )
        for event in events:
            self.coordinator.add_listening_event(
                event,
                self.set_new_target_temperature,
            )

        self.coordinator.register_entity(self)

    # @property
    # def device_class(self) -> str:
    #    """Return device class."""
    #    # https://developers.home-assistant.io/docs/core/entity/binary-sensor#available-device-classes
    #    return ClimateEntity

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers parameter.
        # If your device connects via another device, add via_device parameter with the indentifiers of that device.

        return DeviceInfo(
            name=self._name,
            manufacturer="",
            model="Heizung",
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

    # @property
    # def data(self):
    #    """Return device data."""
    #    return self.coordinator.data.devices[30]

    def get_variables(self):
        return [
            ("CURRENT_TEMPERATURE", self.set_current_temperature),
            ("TARGET_TEMPERATURE", self.set_new_target_temperature),
            ("HEATING_ON", self.set_heating_state),
            ("HEATING_ACTIVE", self.set_heating_active_state),
            ("HEATING_ENABLED", self.set_enabled_state),
        ]

    @property
    def current_temperature(self) -> int | None:
        """Return current temperature."""
        return self._current_temperature

    # def set_current_temperature(self, **kwargs: Any) -> None:
    #    asyncio.run(self.async_set_temperature(kwargs))
    # self._current_temperature = value
    # print(f"New event CURRENT_TEMPERATURE : {value}")
    # self.schedule_update_ha_state()

    # def set_target_temperature(self, value):
    #    print(f"New event TARGET_TEMPERATURE : {value}")
    #    self._target_temperature = value
    #    self.schedule_update_ha_state()

    def set_heating_state_on(self, **kwargs: Any):
        self.set_heating_state(True)

    def set_heating_state_off(self, **kwargs: Any):
        self.set_heating_state(False)

    def set_heating_state(self, my_state):
        self._heating_control_on = my_state
        self.update_hvac_mode()

    def set_heating_is_passive(self, **kwargs: Any):
        self.set_heating_active_state(False)

    def set_heating_is_active(self, **kwargs: Any):
        self.set_heating_active_state(True)

    def set_heating_active_state(self, my_state):
        self._heating_is_active = my_state
        self.update_hvac_mode()

    def set_enabled_state(self, my_state):
        self._enabled = my_state
        self.update_hvac_mode()

    def update_hvac_mode(self):
        if self._heating_control_on is None or self._heating_is_active is None:
            return None

        if not self._heating_control_on:
            self._hvac_mode = HVACMode.OFF

        elif self._heating_is_active:
            self._hvac_mode = HVACMode.HEAT

        else:
            self._hvac_mode = HVACMode.AUTO

        self.schedule_update_ha_state()
        print("Ermittelter HVAC_MODE = ", str(self._hvac_mode))

    def set_new_target_temperature(self, value):
        print("new target temeprature received:", value)
        self._target_temperature = value
        self.update_hvac_mode()

    @property
    def target_temperature_high(self) -> int | None:
        return 25

    @property
    def target_temperature_low(self) -> int | None:
        return 17

    @property
    def target_temperature(self) -> int | None:
        """Return target temperature."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            #    await self.coordinator.async_set_temperature(self._ac_index, temperature)
            self._target_temperature = temperature
            await asyncio.to_thread(
                self.coordinator.connector.send_event(
                    self.ha_library.get_symbolic_event(
                        self.device, "TARGET_TEMPERATURE", temperature
                    )
                )
            )
            self.schedule_update_ha_state()

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac mode."""
        return self._hvac_mode

    @property
    def available(self) -> bool:
        """Return the availability of the entity."""
        print(self._enabled, self._current_temperature)
        return self._enabled and self._current_temperature is not None

    # @property
    # def extra_state_attributes(self) -> dict[str, Any]:
    #    """Return the optional state attributes."""
    #    if (data := self.data) is not None:
    #        return {"error_code": 0}
    #    return {}

    def set_current_temperature(self, value):
        if value > -100 and value < 100:
            self._current_temperature = value
            self.schedule_update_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            commands = self.ha_library.get_symbolic_event(
                self.device, "SET_TARGET_TEMPERATURE", temperature
            )
            self.coordinator.connector.set_destination_address(
                PlatformDefaults.BROADCAST_CCAN_ADDRESS
            )
            for command in commands:
                await asyncio.to_thread(self.coordinator.connector.send_event, command)

            # self._target_temperature = temperature
            # await super().async_set_temperature(**kwargs)
            # self.schedule_update_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the hvac mode."""
        # self._hvac_mode = hvac_mode
        if hvac_mode == HVACMode.AUTO or hvac_mode == HVACMode.HEAT:
            await self.async_turn_on()
        elif hvac_mode == HVACMode.OFF:
            await self.async_turn_off()

    async def async_turn_off(self) -> None:
        """Turn off."""
        commands = self.ha_library.get_symbolic_event(self.device, "TURN_OFF")
        for command in commands:
            await asyncio.to_thread(self.coordinator.connector.send_event, command)

    async def async_turn_on(self) -> None:
        """Turn on."""
        commands = self.ha_library.get_symbolic_event(self.device, "TURN_ON")
        for command in commands:
            await asyncio.to_thread(self.coordinator.connector.send_event, command)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        if (data := self.device) is not None:
            return {"error_code": 0}
        return {}
