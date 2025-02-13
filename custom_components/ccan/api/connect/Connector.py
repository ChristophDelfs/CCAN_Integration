import os
import time
import pickle
import threading
from pathlib import Path

from .UDP_Client import UDP_Client
from api.base.LocateFile import locateFile
from api.events.EventResolver import EventResolver
from api.resolver.ResolverError import ResolverError
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.base.CCAN_Defaults import CCAN_Defaults
from api.base.PlatformDefaults import PlatformDefaults
from api.base.PlatformConfiguration import PlatformConfiguration
from api.base.Report import Report, ReportLevel
from api.events.ApplicationEvent import ApplicationEvent
from .FTP_Services import FTPFileServices
import socket


class Connector:
    # TODO to be checked: -> besser in die defaults?
    max_message_len = 1024

    BUFFER_SIZE = 128 + 10

    def __init__(self, my_server_ip_address, my_server_port=0) -> None:
        self._ccan_defaults = CCAN_Defaults()
        self._event_resolver = EventResolver()

        self._platform_configuration: PlatformConfiguration = None

        self._destination_address = None
        self._server_port = my_server_port
        self._server_address = (my_server_ip_address, self._server_port)
        self._instance_dictionary = None
        self._description_dictionary = None

        self._udp_client: UDP_Client = None
        self._init = False
        self.is_automation_read_from_ftp_server = False

        self._filename: str = None
        self._ftp_services = None

        self._udp_client = UDP_Client(self._server_address)
        self._udp_client.set_client_ccan_address(PlatformDefaults.INVALID_CCAN_ADDRESS)

        self._update_hooks = []

        default_file = PlatformConfiguration.DEFAULT_DEFINITIONS_FILENAME()
        self._ccan_defaults.init_from_pkl(default_file)

        pf = PlatformConfiguration()
        pf.load()
        self._platform_configuration = pf.get()

        # enable ftp services if settings are valid:
        self._ftp_services = FTPFileServices(self._platform_configuration)
        if not self._ftp_services.valid:
            self._ftp_services = None
        else:
            self._udp_client_for_automation_update = UDP_Client(self._server_address)
            self._udp_client_for_automation_update.set_client_ccan_address(
                PlatformDefaults.INVALID_CCAN_ADDRESS
            )

    def get_ccan_defaults(self):
        return self._ccan_defaults

    def get_platform_configuration(self):
        return self._platform_configuration

    def is_connected(self):
        return self._udp_client.is_connected()

    def connect(self):
        result = self._udp_client.connect()
        if self._ftp_services is not None:
            result &= self._udp_client_for_automation_update.connect()

        if result:
            self._event_resolver.set_own_address(self._udp_client.get_ccan_address())
            Report.print(
                ReportLevel.WARN,
                "Found server at address "
                + str(self._udp_client.get_server_address())
                + "\n",
            )
            result = True

        print("connected")
        return result

    def stay_connected(self):
        self._udp_client.stay_connected()
        if self._ftp_services is not None:
            self._udp_client_for_automation_update.stay_connected()
            self._monitor = threading.Thread(target=self.handle_automation_update)
            self._monitor_stop = False
            self._monitor.start()

    def mask_client(self, my_client):
        if not self._udp_client.is_connected():
            raise CCAN_ErrorCode(CCAN_ErrorCode.SERVER_NOT_REACHABLE)
        self._udp_client.mask_client(my_client)

    def unmask_client(self, my_client):
        if not self._udp_client.is_connected():
            raise CCAN_ErrorCode(CCAN_ErrorCode.SERVER_NOT_REACHABLE)
        self._udp_client.unmask_client(my_client)

    def get_own_address(self):
        return self._udp_client.get_ccan_address()

    def disconnect(self):
        # wait some 10ms before saying goodbye
        # this avoids that µC may not notice the disconnect after processing the last command
        time.sleep(0.01)
        self._udp_client.disconnect()
        if self._ftp_services is not None:
            self._monitor_stop = True
            self._udp_client_for_automation_update.disconnect()

    def mark_current_automation_as_invalid(self):
        self.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)
        self.send_event("AUTOMATION_PKL_SERVICE::AUTOMATION_PKL_INVALID()")
        # send it twice:
        self.send_event("AUTOMATION_PKL_SERVICE::AUTOMATION_PKL_INVALID()")

    def announce_new_automation(self, new_automation_file):
        self.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)
        self.send_event(
            f'AUTOMATION_PKL_SERVICE::AUTOMATION_NEW_PKL_VALID("{new_automation_file}")'
        )
        # send it twice:
        self.send_event(
            f'AUTOMATION_PKL_SERVICE::AUTOMATION_NEW_PKL_VALID("{new_automation_file}")'
        )

    def run_on_updated_automation(self, my_hook):
        self._update_hooks.append(my_hook)

    def load_automation(self, my_automation_file):
        self._filename = my_automation_file
        self._init = False
        if self._filename is not None:
            try:
                if os.sep not in self._filename:
                    filename = locateFile(
                        self._filename + ".pkl",
                        self._platform_configuration["CONFIGURATION_PATH"],
                        True,
                    )
                    self._filename = filename[:-4]

                self._read_from_file(f"{self._filename}.pkl")
                self.is_automation_read_from_ftp_server = False
                Report.print(
                    ReportLevel.WARN, "loaded automation " + self._filename + "\n"
                )
                self._init = True
            except FileNotFoundError as err:
                if self._ftp_services is not None:
                        self._read_from_ftp_server(self._filename)
                        self.is_automation_read_from_ftp_server = True
                        self._init = True
                        Report.print(
                            ReportLevel.WARN,
                            f"loaded automation {self._filename} from ftp server\n",
                        )

            if not self._init:
                raise CCAN_Error(
                    CCAN_ErrorCode.FILE_NOT_FOUND,
                    "Provided configuration file "
                    + my_automation_file
                    + " could not be found. Typo in the file name?\n",
                )

        if not self._init:
            raise CCAN_Error(
                CCAN_ErrorCode.ILLEGAL_ARGUMENT,
                "No filename has been provided for automation loading.",
            )

        ApplicationEvent.AUTOMATION_INSTANCE_DICTIONARY = self._instance_dictionary

    def get_automation_source_file(self):
        return self._filename + ".ccan"

    def get_automation_file(self):    
        return self._filename + ".pkl"

    def resolve_event_list(self, my_symbolic_event_list):
        events = []
        for event in my_symbolic_event_list:
            events.append(self.resolve_event(event))
        return events

    def resolve_raw_event(self, my_raw_event):
        try:
            resolved_event = self._event_resolver.resolve_raw_event(my_raw_event)
        except ValueError:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT)
        return resolved_event

    def resolve_event(self, my_symbolic_event):
        try:
            resolved_event = self._event_resolver.resolve_symbolic_event(
                my_symbolic_event
            )
        except ValueError:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT)
        return resolved_event

    def send_event(self, my_event):
        """
        Function ships an event to the connected target.
        The event is described as symbolic expression or a resolved event and supports device, application and protocol events:
        For device events all addressing types are supported. The addressing mode needs to be supplied.
        Examples:

        DeviceEventAddressing:    "DEA my_state_machine::INPUT_TRANSITION(current_state = 2, new_state =4)"
        DirectEventAddressing:    "DIR my_counter::RESTART()"
        OutboundEventAdressing:   "OUT my_counter::RESTART()"
        IndirectEventAddressing:  "IND my_state_machine::INPUT_TRANSITION(current_state = 2, new_state =4)"

        Application Events:       "LIFE_SERVICE::PING()"

        Protocol Events:
        HCAN-Event                "HCAN(path = "SFP/HES")::POWER_GROUP_ON(gruppe= 7)"

        Remarks:
        Parameter arguments can be provided with or with no argument names. If argument names are given, the order of the arguments is corrected if necessary.
        """
        try:
            if isinstance(my_event, str):
                resolved_event = self.resolve_event(my_event)
            else:
                resolved_event = my_event

            self.send_resolved_event(resolved_event)
        except CCAN_Error:
            return False
        return True

    def set_destination_address(self, my_destination):
        self._event_resolver.set_destination_address(my_destination)
        self._destination_address = my_destination

    def get_destination_address(self):
        return self._destination_address

    def send_resolved_event(self, my_resolved_event):
        if len(my_resolved_event.get_sequence()) <= Connector.BUFFER_SIZE:
            return self._udp_client.send(bytes(my_resolved_event.get_sequence()))
        raise CCAN_Error(CCAN_ErrorCode.EVENT_TOO_LONG)

    def wait_for_event(self, my_waiting_time, expected_answer):
        (received_event, index) = self.wait_for_event_list(
            my_waiting_time, [expected_answer]
        )
        return received_event

    def wait_for_event_list(self, my_waiting_time, my_list_of_expected_answers):
        try:
            event_list = self._event_resolver.resolve_event(my_list_of_expected_answers)
        except ResolverError:
            raise CCAN_Error(
                CCAN_ErrorCode.ILLEGAL_ARGUMENT,
                "Error in " + my_list_of_expected_answers,
            )
        if not isinstance(event_list, list):
            event_list = [event_list]
        return self.__wait_for_resolved_event_list(
            my_waiting_time, event_list, self._udp_client
        )

    def wait_for_resolved_event_list(self, my_waiting_time, my_resolved_event_list):
        return self.__wait_for_resolved_event_list(
            my_waiting_time, my_resolved_event_list, self._udp_client
        )

    def __wait_for_resolved_event_list(
        self, my_waiting_time, my_resolved_event_list, my_udp_client
    ):
        remaining_timeout = my_waiting_time
        while True:
            t1 = time.time_ns()
            received_event = self.__receive_event_from_client(
                my_udp_client, remaining_timeout
            )

            # check elapsed time first:
            delta_t = (time.time_ns() - t1) / 1000000000
            remaining_timeout -= delta_t
            if remaining_timeout < 0:
                raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)

            index = 0
            for event in my_resolved_event_list:
                if event == received_event:
                    return (received_event, index)
                else:
                    index += 1

            continue

    def receive_event(self, timeout):
        return self.__receive_event_from_client(self._udp_client, timeout)

    def __receive_event_from_client(self, my_udp_client, timeout):
        try:
            (received_data, sender) = my_udp_client.receive(timeout)
        except (TimeoutError, socket.timeout):
            raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)

        return self._event_resolver.resolve_binary_event(received_data)

    def get_devices(self):
        result_list = []
        for id, device in self._instance_dictionary["DEVICE"]:
            result_list.append(device)
        return result_list

    def get_ha_entities(self):
        result_list = []
        for id, device in self._instance_dictionary["HOME_ASSISTANT"]:
            result_list.append(device)
        return result_list

    def get_variable_names(self):
        if self._instance_dictionary is None:
            raise CCAN_Error(
                CCAN_ErrorCode.COMMON_AUTOMATION_NOT_AVAILABLE,
                "It is not possible to access an automation variable if no automation is defined.",
            )

        variables = self._instance_dictionary["VARIABLE"]
        names = []
        for index, variable in variables:
            names.append(variable.get_name())
        return names

    def identify_variable(self, my_name):
        try:
            [device_name, var_name] = my_name.split("::", 2)
        except ValueError:
            raise CCAN_Error(
                CCAN_ErrorCode.ILLEGAL_ARGUMENT,
                my_name + " does not follow the form <device_name>::<variable_name>.",
            )

        if self._instance_dictionary is None:
            raise CCAN_Error(
                CCAN_ErrorCode.COMMON_AUTOMATION_NOT_AVAILABLE,
                "It is not possible to access an automation variable if no automation is defined.",
            )

        try:
            resolved_device = self._instance_dictionary["DEVICE"].get_entry_by_name(
                device_name
            )
        except KeyError:
            raise CCAN_Error(
                CCAN_ErrorCode.ILLEGAL_ARGUMENT,
                "Device name " + device_name + " does not exist.",
            )

        if resolved_device.is_template() is True:
            raise CCAN_Error(
                CCAN_ErrorCode.ILLEGAL_ARGUMENT,
                "Referenced device "
                + device_name
                + " is a template. Currently not supported",
            )

        controller_name = resolved_device.get_description_list("CONNECTION")[0]

        # get variables:
        result = None
        variable_list = resolved_device.get_description_list("VARIABLE")
        for variable in variable_list:
            if variable.get_name() == my_name:
                variable_id = variable.get_value()
                return (controller_name, variable_id)

        raise CCAN_Error(
            CCAN_ErrorCode.ILLEGAL_ARGUMENT,
            "Variable name "
            + var_name
            + " does not exist for the device "
            + device_name
            + ".",
        )

    def _write(self, my_file):
        pickle.dump(self._description_dictionary, my_file)
        pickle.dump(self._instance_dictionary, my_file)

    def _read_from_ftp_server(self, my_filename):
        filename = os.path.basename(my_filename)
        local_filename = self._ftp_services.pull_from_ftp_server(filename)
        self._read_from_file(local_filename)

    def _read_from_file(self, my_filename):
        try:
            with open(my_filename, "rb") as f:
                self._description_dictionary = pickle.load(f)
                self._instance_dictionary = pickle.load(f)
        except Exception as ex:
            pass

        self._event_resolver.set_automation(
            self._description_dictionary, self._instance_dictionary
        )

    def get_instance_dictionary(self):
        return self._instance_dictionary

    def get_description_dictionary(self):
        return self._description_dictionary

    def get_automation_filename(self):
        return self._filename

    def handle_automation_update(self):
        pkl_invalid = False
        listen_to_events = self._event_resolver.resolve_event(
            [
                "AUTOMATION_PKL_SERVICE::AUTOMATION_PKL_INVALID()",
                "AUTOMATION_PKL_SERVICE::AUTOMATION_NEW_PKL_VALID()",
            ]
        )
        while not self._monitor_stop:
            try:
                received_event, index = self.__wait_for_resolved_event_list(
                    self._platform_configuration["RESPONSE_WAITING_TIME"],
                    listen_to_events,
                    self._udp_client_for_automation_update,
                )

                if index == 0 and not pkl_invalid:
                    self._event_resolver.set_automation(None, None)
                    Report.print(
                        ReportLevel.WARN,
                        "Current automation file has been invalidated. Only application events will be received from now on.\n",
                    )
                    pkl_invalid = True
                if index == 1 and pkl_invalid:
                    pkl_filename = received_event.get_parameter_values()[0]
                    self.load_automation(pkl_filename[1:-1])
                    pkl_invalid = False

                    # run registered hooks:
                    for hook in self._update_hooks:
                        hook()
            except CCAN_Error:
                pass
