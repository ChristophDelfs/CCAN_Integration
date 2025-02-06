"""CCAN integration using DataUpdateCoordinator."""

from dataclasses import dataclass
from datetime import timedelta
import logging
import asyncio
import time
import threading
import contextlib
from datetime import datetime
from enum import StrEnum

# to be removed:
import random

from threading import Event

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# from homeassistant.helpers.entity import async_update_ha_state
from homeassistant.helpers.entity import Entity

# from .api import API, APIAuthError, Device, DeviceType
from .const import DEFAULT_SCAN_INTERVAL

# from .PyCCAN.api.resolver.ResolverElements import ResolvedDeviceInstance


# add CCAN Integration
import os
import sys

import pathlib

cwd = str(pathlib.Path(__file__).parent.resolve())
os.environ["CCAN"] = cwd
if cwd not in sys.path:
    sys.path.insert(1, cwd)

from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.connect.Connector import Connector
from api.cli.interactions.automation.AutomationBase import AutomationBase
from api.HA_Integration.HA_Library import HA_Library

_LOGGER = logging.getLogger(__name__)


class CCAN_Coordinator(DataUpdateCoordinator):
    """Coordinator for CCAN integration"""

    # data: ExampleAPIData
    # api: API = None
    # entities: set = {}
    # values: set[float | bool] = {}

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # self.update_thread = None

        self.hass = hass
        self._stop_event: Event = Event()
        self.update_thread = None
        self.ready: bool = False  # connected & automation & CCAN_Pseudo devices loaded
        self.ready_to_listen: bool = (
            False  # similar to ready, but additionally CCAN read thread is prepared
        )

        self.initialize_count: int = (
            0  # all created HA device have registered their events in coordinator
        )
        self.initialized: bool = False
        self.connector: Connector = None
        self._automation_base: AutomationBase = None
        self._collected_listening_event_map = {}
        self._registered_entities: list[Entity] = []

        # Set variables from values entered in config flow setup
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]

        # set variables from options.  You need a default here incase options have not been set
        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        self.ha_library = None

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            # Using config option here but you can just use a value.
            update_interval=timedelta(seconds=self.poll_interval),
        )

    @staticmethod
    async def validate_connection(host: str, port: int):
        connector = await asyncio.to_thread(Connector, host, port)
        # await asyncio.to_thread(connector.setup)
        await asyncio.to_thread(connector.connect)
        return connector.is_connected()

    async def connect(self):
        _LOGGER.info("Create Connector")
        self.connector = await asyncio.to_thread(Connector, self.host, self.port)
        _LOGGER.info("..connect")
        await asyncio.to_thread(self.connector.connect)
        _LOGGER.info("..connect done")
        if self.connector.is_connected():
            _LOGGER.info(
                "CCAN Integration connected to CCAN server using CCAN address %d",
                self.connector.get_own_address(),
            )
            if await self.read_device_information_from_automation():
                _LOGGER.info(
                    "CCAN Integration loaded automation file %s",
                    self.connector.get_automation_file(),
                )

                await asyncio.to_thread(self.connector.stay_connected)

                # self.connector.run_on_updated_automation(self.update_automation_information)

                self.update_thread = threading.Thread(
                    target=self.read_from_ccan_network
                )
                self.update_thread.start()

                # just executed at the beginning in background:
                initialize_job = threading.Thread(target=self.initialize_entity_state)
                initialize_job.start()

            else:
                _LOGGER.error(
                    "CCAN Integration could not load automation file. Unable to proceed!"
                )

        else:
            _LOGGER.error(
                "CCAN Integration failed to connected to CCAN server using CCAN address %d",
                self.connector.get_own_address(),
            )

    @property
    def connected(self):
        return self.coordinator.is_connected()

    async def disconnect(self):
        self._stop_event.set()
        await asyncio.sleep(0.3)

        await asyncio.to_thread(self.connector.disconnect)
        self.ready = False

    async def read_device_information_from_automation(self):
        """Get list of devices from automation file."""

        _LOGGER.info("Lese aus gelesener Automation!! -1-")
        if not self.connector.is_connected():
            return False
        try:
            self._automation_base = await asyncio.to_thread(
                AutomationBase, self.connector, 0.2, False, "MIN"
            )
            _LOGGER.info("Lese aus gelesener Automation!! -2-")
        except CCAN_Error as err:
            _LOGGER.error("CCAN Exception during setup %s", str(err))
            return False

        # simplify access to devices:
        self.ha_library = HA_Library(self.connector.get_instance_dictionary())

        self.ready = True
        return True

    # async def setup(self):
    #    if not self._setup_done:
    #        await API.stay_connected()###

    #        self.update_thread = threading.Thread(target=self.read_from_ccan_network)
    #        self.update_thread.start()

    #        self._setup_done = True

    # def is_connected(self):
    #    return self._connector.is_connected()

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        if not self.connector.is_connected:
            raise UpdateFailed("No connection with host")

        if not self.ready:
            raise UpdateFailed("Could not read automation data.")

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return None

    def get_controller_name(self):
        return self.host.replace(".", "_")

    # def get_device_by_id(
    #    self, device_type: ResolvedDeviceInstance, device_id: int
    # ) -> Device | None:
    #    """Return device by device id."""
    #    # Called by the binary sensors and sensors to get their updated data from self.data
    #    try:
    #        return [
    #            device
    #            for device in self.data.devices
    #            if device.device_type == device_type and device.device_id == device_id
    #        ][0]
    #    except IndexError:
    #        return None
    def add_listening_event(self, my_new_event: str, my_method):
        try:
            existing_methods = self._collected_listening_event_map[my_new_event]
            existing_methods.apppend(my_method)
        except KeyError:
            self._collected_listening_event_map[my_new_event] = [my_method]

    def register_entity(self, my_entity):
        self._registered_entities.append(my_entity)

    def initialize_entity_state(self):
        """Trigger that all devices respond with their state."""
        # wait for all devices being registered and CCAN read thead is listening:
        type_count = self.ha_library.get_number_of_device_types()
        while self.initialize_count != type_count:
            time.sleep(1)

        for entity in self._registered_entities:
            if self._stop_event.is_set():
                return
            for variable, method in entity.get_variables():
                method(
                    self.ha_library.get_variable_value(
                        self.connector, entity.device, variable, 0.2
                    )
                )

        self.initialized = True

    def update_automation_information(self):
        # string representation:
        time1 = datetime.now()
        list_of_events = list(self._collected_listening_event_map.keys())
        # print(list_of_events)
        # binary representation (faster to)
        list_of_binary_events = self.connector.resolve_event_list(list_of_events)
        time2 = datetime.now()
        _LOGGER.warning(
            "Conversion time for listening events took %s seconds",
            (time2 - time1).total_seconds(),
        )
        return list_of_events, list_of_binary_events

    def read_from_ccan_network(self):
        """Thread to monitor all registered input events and call registered methods."""
        # wait for all devices being registered:

        while not self.initialized:
            time.sleep(0.1)

        list_of_events, list_of_binary_events = self.update_automation_information()
        self.ready_to_listen = True

        while True:
            # receive:
            received_event = None
            if self._stop_event.is_set():
                return
            try:
                received_event, index = self.connector.wait_for_event_list(
                    0.1,
                    list_of_binary_events,  # Interaction.timeout ??
                )

                # call entity with appropriate method
                if received_event is not None:
                    received_string_event = list_of_events[index]
                    # call entity:
                    my_methods = self._collected_listening_event_map[
                        received_string_event
                    ]
                    parameters = received_event.get_parameter_values()
                    if parameters is None:
                        for my_method in my_methods:
                            my_method()
                    else:
                        for my_method in my_methods:
                            # print(f"Call {my_method} mit Parameter {parameters[0]}")
                            my_method(parameters[0])

            except CCAN_Error as ex:
                if ex.get_code() != CCAN_ErrorCode.TIME_OUT:
                    _LOGGER.error("CCAN Thread with unexpected error: %s", str(ex))
                    return  ##
