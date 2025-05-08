import binascii
import pickle
from collections import namedtuple

# from api.UDP_Client import UDP_Client

from api.resolver.Definitions import ParamListInfo
from api.resolver.Definitions import EventDescriptor

from api.events.EventParser import CLI_EventParser
from api.events.RawEvent import RawEvent
from api.events.ApplicationEvent import ApplicationEvent
from api.events.DeviceEvent import DeviceEvent
from api.events.HCAN_Event import HCAN_Event
from api.cli.CliError import CliError as CliError
from api.cli.CliError import CliErrorCode as CliErrorCode
from api.base.PlatformDefaults import PlatformDefaults


class EventResolver:
    def __init__(self, filename=None):
        self.__init = False
        self.__ccan_address = PlatformDefaults.INVALID_CCAN_ADDRESS
        self.__destination_address = PlatformDefaults.INVALID_CCAN_ADDRESS

        self._instance_dictionary = None
        self._description_dictionary = None
        application_event_dictionary = {}
        ApplicationEventMapDescriptor = namedtuple(
            "ApplicationEventMapDescriptor", "event_list service_id"
        )

        new_app_event_list = []
        new_app_event_list.append(
            EventDescriptor(name="ENABLE_VERBOSE_EVENTS", id=0, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ENABLE_VERBOSE_EVENTS_ACK", id=1, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="DISABLE_VERBOSE_EVENTS", id=2, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="DISABLE_VERBOSE_EVENTS_ACK", id=3, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(
                name="ENABLE_APPLICATION_EVENTS_ONLY", id=4, parameters=None
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="ENABLE_APPLICATION_EVENTS_ONLY_ACK", id=5, parameters=None
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DISABLE_APPLICATION_EVENTS_ONLY", id=6, parameters=None
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DISABLE_APPLICATION_EVENTS_ONLY_ACK", id=7, parameters=None
            )
        )

        debug_parameters = ParamListInfo(
            parameter_name_list=["message"],
            parameter_type_list=["STRING"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="DEBUG", id=8, parameters=debug_parameters)
        )

        new_app_event_list.append(
            EventDescriptor(
                name="ENGINE_THREAD_FAILURES_REQUEST", id=9, parameters=None
            )
        )

        thread_failure_parameters = ParamListInfo(
            parameter_name_list=["slow_thread_failures", "fast_thread_failures"],
            parameter_type_list=["UINT16", "UINT16"],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="ENGINE_THREAD_FAILURES_REPLY",
                id=10,
                parameters=thread_failure_parameters,
            )
        )

        application_event_dictionary["ENGINE_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=0
        )

        ####################

        new_app_event_list = []
        # ping_parameters =  ParamListInfo(parameter_name_list=["index"], parameter_type_list = [ "UINT32"],dimension_list=["Scalar"])
        new_app_event_list.append(EventDescriptor(name="PING", id=0, parameters=None))
        new_app_event_list.append(EventDescriptor(name="PONG", id=1, parameters=None))

        uptime_parameters = ParamListInfo(
            parameter_name_list=["seconds"],
            parameter_type_list=["UINT32"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="UPTIME", id=2, parameters=uptime_parameters)
        )

        new_app_event_list.append(
            EventDescriptor(name="RESET_REQUEST", id=3, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="RESET_ACK", id=4, parameters=None)
        )

        new_app_event_list.append(
            EventDescriptor(name="DEGRADATION_STATUS_REQUEST", id=5, parameters=None)
        )

        degradation_item_parameter_list = ParamListInfo(
            parameter_name_list=["id", "type", "status", "code"],
            parameter_type_list=["UINT16", "UINT8", "UINT8", "UINT8"],
            dimension_list=["Scalar", "Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DEGRADATION_STATUS_REPLY_ITEM",
                id=6,
                parameters=degradation_item_parameter_list,
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DEGRADATION_STATUS_REPLY_COMPLETED", id=7, parameters=None
            )
        )

        # client_available_parameters =  ParamListInfo(parameter_name_list=["ccan address","name"], parameter_type_list = [ "UINT16","STRING"],dimension_list=["Scalar","Scalar"])
        # new_app_event_list.append(EventDescriptor(name="CLIENT_AVAILABLE",  id =  8, parameters = client_available_parameters ))
        new_app_event_list.append(
            EventDescriptor(name="PROCESSOR_LOAD_REQUEST", id=8, parameters=None)
        )
        processor_load_item_parameter_list = ParamListInfo(
            parameter_name_list=["load", "load_max"],
            parameter_type_list=["UINT8", "UINT8"],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="PROCESSOR_LOAD_REPLY",
                id=9,
                parameters=processor_load_item_parameter_list,
            )
        )

        led_parameters = ParamListInfo(
            parameter_name_list=["id", "mode"],
            parameter_type_list=["UINT8", "UINT8"],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="SET_BOARD_LED", id=10, parameters=led_parameters)
        )
        new_app_event_list.append(
            EventDescriptor(name="SET_BOARD_LED_ACK", id=11, parameters=None)
        )

        new_app_event_list.append(
            EventDescriptor(name="LOCK_BOOTLOADER", id=12, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="LOCK_BOOTLOADER_ACK", id=13, parameters=None)
        )

        new_app_event_list.append(
            EventDescriptor(name="UPTIME_REQUEST", id=14, parameters=None)
        )
        uptime_parameters = ParamListInfo(
            parameter_name_list=["seconds"],
            parameter_type_list=["UINT32"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(

            EventDescriptor(name="UPTIME_REPLY", id=15, parameters=uptime_parameters)
        )

        new_app_event_list.append(
            EventDescriptor(name="TIME_REQUEST", id=16, parameters=None)
        )
       
        time_parameters = ParamListInfo(
            parameter_name_list=["seconds"],
            parameter_type_list=["UINT64"],
            dimension_list=["Scalar"],
        )

        new_app_event_list.append(
            EventDescriptor(name="TIME_REPLY", id=17, parameters=time_parameters)
        )

        new_app_event_list.append(
            EventDescriptor(name="STARTUP_ENGINE", id=20, parameters=None)
        )

        reset_reason_parameters = ParamListInfo(
            parameter_name_list=["CODE"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="CONTROLLER_RESET", id=21, parameters=reset_reason_parameters
            )
        )

        application_event_dictionary["LIFE_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=1
        )

        #######################

        #######################

        new_app_event_list = []
        new_app_event_list.append(
            EventDescriptor(name="APP_COOKIE_ERROR", id=0, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ENGINE_COOKIE_ERROR", id=1, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ENGINE_CONFIG_VERSION_ERROR", id=3, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ENGINE_CONFIG_OK", id=4, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="GET_SW_ID", id=6, parameters=None)
        )
        sw_id_parameter = ParamListInfo(
            parameter_name_list=["value"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="SW_ID", id=7, parameters=sw_id_parameter)
        )
        new_app_event_list.append(
            EventDescriptor(name="GET_VERSION", id=8, parameters=None)
        )
        version_parameters = ParamListInfo(
            parameter_name_list=[
                "sw_major",
                "sw_minor",
                "sw_patch",
                "config_major",
                "config_minor",
                "config_patch",
            ],
            parameter_type_list=[
                "UINT16",
                "UINT16",
                "UINT16",
                "UINT16",
                "UINT16",
                "UINT16",
            ],
            dimension_list=["Scalar", "Scalar", "Scalar", "Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="GET_VERSION_REPLY", id=9, parameters=version_parameters
            )
        )
        new_app_event_list.append(
            EventDescriptor(name="ERASE_CONFIG", id=10, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ERASE_CONFIG_ACK", id=11, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ERASE_CONFIG_NACK", id=12, parameters=None)
        )

        request_address_parameter_list = ParamListInfo(
            parameter_name_list=["uuid"],
            parameter_type_list=["UINT8"],
            dimension_list=["Vector"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="REQUEST_ADDRESS", id=20, parameters=request_address_parameter_list
            )
        )
        request_address_reply_parameter_list = ParamListInfo(
            parameter_name_list=["uuid", "ccan_address"],
            parameter_type_list=["UINT8", "UINT16"],
            dimension_list=["Vector", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="REQUEST_ADDRESS_REPLY",
                id=21,
                parameters=request_address_reply_parameter_list,
            )
        )

        new_app_event_list.append(
            EventDescriptor(name="SHORT_INFO_REQUEST", id=30, parameters=None)
        )
        short_info_request_parameter_list = ParamListInfo(
            parameter_name_list=["uuid", "crc"],
            parameter_type_list=["UINT8", "UINT64"],
            dimension_list=["Vector", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="SHORT_INFO_REQUEST_REPLY",
                id=31,
                parameters=short_info_request_parameter_list,
            )
        )

        request_info_parameter_list = ParamListInfo(
            parameter_name_list=["update_section"],
            parameter_type_list=["UINT16"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="INFO_REQUEST", id=40, parameters=request_info_parameter_list
            )
        )

        configuration_parameter_list = ParamListInfo(
            parameter_name_list=[
                "sw_version_major",
                "sw_version_minor",
                "sw_version_patch",
                "date",
                "filename",
            ],
            parameter_type_list=["UINT16", "UINT16", "UINT16", "UINT32", "STRING"],
            dimension_list=["Scalar", "Scalar", "Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="CONFIGURATION_INFO",
                id=41,
                parameters=configuration_parameter_list,
            )
        )

        bootloader_parameter_list = ParamListInfo(
            parameter_name_list=[
                "sw_version_major",
                "sw_version_minor",
                "sw_version_patch",
                "date",
                "filename",
            ],
            parameter_type_list=["UINT16", "UINT16", "UINT16", "UINT32", "STRING"],
            dimension_list=["Scalar", "Scalar", "Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="BOOTLOADER_INFO", id=42, parameters=bootloader_parameter_list
            )
        )

        firmware_parameter_list = ParamListInfo(
            parameter_name_list=[
                "sw_version_major",
                "sw_version_minor",
                "sw_version_patch",
                "date",
                "filename",
            ],
            parameter_type_list=["UINT16", "UINT16", "UINT16", "UINT32", "STRING"],
            dimension_list=["Scalar", "Scalar", "Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="FIRMWARE_INFO", id=43, parameters=firmware_parameter_list
            )
        )

        # new_app_event_list.append(EventDescriptor(name="UNSUPPORTED_COMMAND",  id =  10, parameters = None))

        application_event_dictionary["CONFIG_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=3
        )

        ###########################

        new_app_event_list = []
        download_descriptor = ParamListInfo(
            parameter_name_list=[
                "Type",
                "Version_Major",
                "Version_Minor",
                "Version_Patch",
                "Size",
                "CRC",
                "CONTROLLER_CRC",
                "Date",
                "Filename",
                "Lock_flag",
            ],
            parameter_type_list=[
                "UINT8",
                "UINT16",
                "UINT16",
                "UINT16",
                "UINT32",
                "UINT32",
                "UINT32",
                "UINT32",
                "STRING",
                "BOOL",
            ],
            dimension_list=[
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
                "Scalar",
            ],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DOWNLOAD_REQUEST", id=10, parameters=download_descriptor
            )
        )
        ack_answer = ParamListInfo(
            parameter_name_list=["page_size", "already_up_to_date"],
            parameter_type_list=["UINT32", "BOOL"],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_ACK", id=11, parameters=ack_answer)
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_READY_TO_RUMBLE", id=15, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_NACK", id=19, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="FILE_TOO_BIG", id=25, parameters=None)
        )
        parameters_chunk = ParamListInfo(
            parameter_name_list=["data"],
            parameter_type_list=["UINT8"],
            dimension_list=["Vector"],
        )
        new_app_event_list.append(
            EventDescriptor(name="FILE_INVALID", id=26, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(
                name="VERSION_MISMATCH_WITH_FIRMWARE", id=27, parameters=None
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="VERSION_MISMATCH_WITH_BOOTLOADER", id=28, parameters=None
            )
        )

        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_CHUNK", id=21, parameters=parameters_chunk)
        )
        parameters_ack = ParamListInfo(
            parameter_name_list=["chunk_count"],
            parameter_type_list=["UINT32"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_CHUNK_ACK", id=12, parameters=parameters_ack)
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DOWNLOAD_CHUNK_NACK", id=13, parameters=parameters_ack
            )
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_END", id=22, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_END_ACK", id=14, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_FLASH_ERASE_FAILURE", id=50, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DOWNLOAD_FLASH_PROGRAM_FAILURE", id=51, parameters=None
            )
        )
        new_app_event_list.append(
            EventDescriptor(name="DOWNLOAD_TIME_OUT", id=52, parameters=None)
        )

        application_event_dictionary["DOWNLOAD_SERVICE"] = (
            ApplicationEventMapDescriptor(event_list=new_app_event_list, service_id=4)
        )

        new_app_event_list = []
        parameters = ParamListInfo(
            parameter_name_list=["Index"],
            parameter_type_list=["UINT32"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="KEY_PRESSED", id=0, parameters=parameters)
        )
        new_app_event_list.append(
            EventDescriptor(name="KEY_RELEASED", id=1, parameters=parameters)
        )
        parameters2 = ParamListInfo(
            parameter_name_list=["Index"],
            parameter_type_list=["UINT8"],
            dimension_list=["Vector"],
        )
        new_app_event_list.append(
            EventDescriptor(name="OUTPUT_STATUS", id=2, parameters=parameters2)
        )
        application_event_dictionary["REMOTE_IO_SERVICE"] = (
            ApplicationEventMapDescriptor(event_list=new_app_event_list, service_id=10)
        )

        new_app_event_list = []
        my_func = self.__derive_parameter_type_from_variable_id
        variable_parameters = ParamListInfo(
            parameter_name_list=["ID", "VALUE"],
            parameter_type_list=["UINT16", my_func],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="SET", id=0, parameters=variable_parameters)
        )
        variable_parameters2 = ParamListInfo(
            parameter_name_list=["ID"],
            parameter_type_list=["UINT16"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="GET", id=1, parameters=variable_parameters2)
        )
        new_app_event_list.append(
            EventDescriptor(name="GET_RESULT", id=2, parameters=variable_parameters)
        )
        application_event_dictionary["VARIABLE_SERVICE"] = (
            ApplicationEventMapDescriptor(event_list=new_app_event_list, service_id=11)
        )

        ds1820_timing_parameters = ParamListInfo(
            parameter_name_list= ["PULLDOWN_PERIOD","FLOATING_PERIOD_BEFORE_SAMPLING","FLOATING_PERIOD_AFTER_SAMPLING","RECOVERY_PERIOD"],
            parameter_type_list=["UINT8","UINT8","UINT8","UINT8"],
            dimension_list=["Scalar","Scalar","Scalar","Scalar"],
        )


        new_app_event_list = []
        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_SET_READ_TIMINGS", id=0, parameters= ds1820_timing_parameters
            )
        )
       
        ds1820_parameters = ParamListInfo(
            parameter_name_list=["Pin"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_SEARCH", id=1, parameters=ds1820_parameters
            )
        )
        ds1820_parameters2 = ParamListInfo(
            parameter_name_list=["ROM_CODES","POWER_SUPPLY_TYPE"],
            parameter_type_list=["UINT64","UINT8"],
            dimension_list=["Vector","Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_SEARCH_RESULT", id=2, parameters=ds1820_parameters2
            )
        )

        ds1820_instant_mesasurement_parameters = ParamListInfo(
            parameter_name_list=["PIN","ROM_CODE"],
            parameter_type_list=["UINT8","UINT64"],
            dimension_list=["Scalar","Scalar"],
        )

        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_REQUEST_INSTANT_MEASUREMENT", id=3, parameters= ds1820_instant_mesasurement_parameters
            )
        )

        ds1820_instant_mesasurement_parameters = ParamListInfo(
            parameter_name_list=["PIN","ROM_CODE"],
            parameter_type_list=["UINT8","UINT64"],
            dimension_list=["Scalar","Scalar"],
        )

        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_GET_LAST_TEMPERATURE", id=4, parameters= ds1820_instant_mesasurement_parameters
            )
        )

        ds1820_instant_mesasurement_parameters = ParamListInfo(
            parameter_name_list=["TEMPERATURE","SCRATCH_PAD"],
            parameter_type_list=["FLOAT","UINT8"],
            dimension_list=["Scalar","Vector"],
        )

        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_GET_LAST_TEMPERATURE_REPLY", id=5, parameters= ds1820_instant_mesasurement_parameters
            )
        )


        ds1820_failure_reply_parameters = ParamListInfo(
            parameter_name_list=["ERROR_CODE"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )

        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_RESULT_CODE", id=6, parameters= ds1820_failure_reply_parameters
            )
        )

        ds1820_parameters3 = ParamListInfo(
            parameter_name_list=["Status"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )

        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_DETECTION_ERROR",
                id=7,
                parameters=ds1820_parameters3,
            )
        )
        new_app_event_list.append(
            EventDescriptor(
                name="DS1820_SERVICE_PIN_NOT_AVAILABLE", id=8, parameters=None
            )
        )

        application_event_dictionary["DS1820_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=12
        )


        new_app_event_list = []
        # ds1820_parameters =  ParamListInfo(parameter_name_list=["Pin"], parameter_type_list = [ "UINT8"],dimension_list=["Scalar"])
        new_app_event_list.append(EventDescriptor(name="SEARCH", id=0, parameters=None))
        expander_param = ParamListInfo(
            parameter_name_list=["DETECTED_BANKS", "DETECTED_TYPES", "NAMES"],
            parameter_type_list=["UINT8", "UINT16", "STRING"],
            dimension_list=["Vector", "Vector", "Vector"],
        )
        new_app_event_list.append(
            EventDescriptor(name="SEARCH_RESULT", id=1, parameters=expander_param)
        )
        expander_param3 = ParamListInfo(
            parameter_name_list=["ADDRESS", "EXPANDER_TYPE", "NAME"],
            parameter_type_list=["UINT8", "UINT16", "STRING"],
            dimension_list=["Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="INITIALIZE_EXPANDER32", id=2, parameters=expander_param3
            )
        )
        new_app_event_list.append(
            EventDescriptor(name="ACCESS_OK", id=3, parameters=None)
        )
        new_app_event_list.append(
            EventDescriptor(name="ACCESS_ERROR", id=4, parameters=None)
        )
        application_event_dictionary["EXPANDER_SERVICE"] = (
            ApplicationEventMapDescriptor(event_list=new_app_event_list, service_id=13)
        )

        new_app_event_list = []
        new_app_event_list.append(
            EventDescriptor(name="MEMORY_USAGE_REQUEST", id=0, parameters=None)
        )
        memory_usage_parameter_list = ParamListInfo(
            parameter_name_list=["FREE RAM", "USED_RAM"],
            parameter_type_list=["UINT32", "UINT32"],
            dimension_list=["Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="MEMORY_USAGE_RESULT", id=1, parameters=memory_usage_parameter_list
            )
        )
        application_event_dictionary["MEMORY_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=14
        )

        new_app_event_list = []
        parameters = ParamListInfo(
            parameter_name_list=["UNIX_TIME", "PRIORITY", "SOURCE"],
            parameter_type_list=["UINT64", "UINT8", "UINT16"],
            dimension_list=["Scalar", "Scalar", "Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="TIME_UPDATE", id=0, parameters=parameters)
        )
        application_event_dictionary["TIME_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=15
        )



        new_app_event_list = []
        new_app_event_list.append(
            EventDescriptor(name="AUTOMATION_PKL_INVALID", id=0, parameters=None)
        )


        parameters = ParamListInfo(
            parameter_name_list=["PKL_FILE"],
            parameter_type_list=["STRING"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(name="AUTOMATION_NEW_PKL_VALID", id=1, parameters=parameters)
        )

        application_event_dictionary["AUTOMATION_PKL_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=98
        )


        new_app_event_list = []
        event_flood_parameters = ParamListInfo(
            parameter_name_list=["REPETITIONS"],
            parameter_type_list=["UINT8"],
            dimension_list=["Scalar"],
        )
        new_app_event_list.append(
            EventDescriptor(
                name="FLOOD_WITH_EVENTS", id=0, parameters=event_flood_parameters
            )
        )
        application_event_dictionary["DEBUG_SERVICE"] = ApplicationEventMapDescriptor(
            event_list=new_app_event_list, service_id=99
        )

        ApplicationEvent.APPLICATION_EVENT_DICTIONARY = application_event_dictionary

    def set_own_address(self, my_own_address):
        self.__ccan_address = my_own_address

    def set_destination_address(self, my_destination_address):
        self.__destination_address = my_destination_address

    def get_destination_address(self):
        return self.__destination_address

    def set_automation(self, my_description_dictionary, my_instance_dictionary):
        self._description_dictionary = my_description_dictionary
        self._instance_dictionary = my_instance_dictionary       
        
        if my_description_dictionary is None or my_instance_dictionary is None:
            self.__init = False
        else:
            self.__init = True

    def resolve_event(self, my_event_list):
        if not isinstance(my_event_list, list):
            my_event_list = [my_event_list]

        event_list = []
        for event in my_event_list:
            if isinstance(event, str):
                event_list.append(self.resolve_symbolic_event(event))
            else:             
                event_list.append(event)

        if len(event_list) == 1:
            return event_list[0]

        return event_list

    def resolve_binary_event(self, my_raw_data):
        raw_event = RawEvent(list(my_raw_data))
        return self.resolve_raw_event(raw_event)

    def resolve_raw_event(self, raw_event):
        if raw_event.get_addressing_type().is_device_event() and self.__init:
            return DeviceEvent(
                raw_event,
                self._instance_dictionary["DEVICE"],
                self._description_dictionary["DEVICE"],
            )
        if raw_event.get_addressing_type().is_application_event():
            if self.__init:
                dict = self._instance_dictionary["APP"]
            else:
                dict = None
            return ApplicationEvent(raw_event, self.__ccan_address)
        if raw_event.get_addressing_type().is_external_protocol_event():
            if self._instance_dictionary is not None:
                return HCAN_Event(
                    raw_event,
                    self._instance_dictionary["PROTOCOL"]
                    .get_entry_by_name("HCAN")
                    .get_protocol_map(),
                    self,
                )

        # ignore event if resolving is not supported
        return None

    def resolve_symbolic_event(self, my_symbolic_event):
        parsed_event = CLI_EventParser(my_symbolic_event)
        if parsed_event.is_device_event()  and self.__init:
            return DeviceEvent(
                parsed_event,
                self._instance_dictionary["DEVICE"],
                self._description_dictionary["DEVICE"],
            )
        elif parsed_event.is_application_event():
            ApplicationEvent.INSTANCE_DICTIONARY = self._instance_dictionary           
            try:
                return ApplicationEvent(
                    parsed_event,
                    self.__ccan_address,
                    self.__destination_address,
                    self.__ccan_address,                  
                )
            except TypeError:
                raise CliError(
                    CliErrorCode.ILLEGAL_ARGUMENT,
                    "Application Event "
                    + my_symbolic_event
                    + " could not be resolved.",
                )
        elif parsed_event.is_hcan_event():
            return HCAN_Event(
                parsed_event,
                100,
                self._instance_dictionary["PROTOCOL"]
                .get_entry_by_name("HCAN")
                .get_protocol_map(),
            )
        raise CliError(
            CliErrorCode.ILLEGAL_ARGUMENT,
            "Event "
            + my_symbolic_event
            + " could not be mapped to an event type. Resolving canceled..",
        )

    def __derive_parameter_type_from_variable_id(self, my_param):
        if not self.__init:
            raise ValueError

        var_tab = self._instance_dictionary["VARIABLE"]
        for var_id, var in var_tab:
            if var_id == int(my_param):
                return str(var.get_format())
        print("Internal Error: wrong 'last value'..")
        raise ValueError

    def __derive_reset_reason_from_code(self, my_param):
        code = int(my_param)
        if code == 0:
            return "POWER_ON"
        if code == 1:
            return "PIN_RESET"
        if code == 2:
            return "BROWN_OUT"
        if code == 3:
            return "SOFTWARE"
        if code == 4:
            return "WATCHDOG"
        if code == 5:
            return "LOCKED - UNRECOVERABLE_EXCEPTION"
        if code == 6:
            return "WAKE_LOW_POWER"
        if code == 7:
            return "ACCESS_ERROR"
        if code == 8:
            return "BOOT_ERROR"
        if code == 9:
            return "MULTIPLE_RESET_REASONS"
        if code == 10:
            return "PLATFORM_SPECIFIC_REASON"
        return "UNKNOWN_REASON"
