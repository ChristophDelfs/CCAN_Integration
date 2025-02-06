from enum import Enum


class CCAN_ErrorCode(Enum):
    OK = 0
    TIME_OUT = 1
    SERVER_NOT_REACHABLE = 2
    DESTINATION_NOT_REACHABLE = 3
    BROADCAST_NO_RESPONSE = 4

    FILE_NOT_FOUND = 8
    FILE_INVALID = 9
    TARGET_UP_TO_DATE = 10
    FLASH_ERASE_FAILURE = 11
    UPDATE_FAILURE = (12,)

    PROTOCOL_EVENT_INVALID = (13,)

    ILLEGAL_EXPANDER_TYPE = 15
    EXPANDER_INITIALIZATION_FAILED = 16

    DS1820_NO_SENSOR_DETECTED = 20
    DS1820_GND_AND_DATA_ARE_CONNECTED = 21
    DS1820_SENSING_ERROR = 22
    DS1820_PIN_NOT_AVAILABLE = 23

    DEGRADATION_STATUS_NOT_RESOLVABLE = (30,)

    CONFIGURATION_NOT_AVAILABLE = (40,)
    UNEXPECTED_CONTROLLER_NOT_IN_AUTOMATION = (41,)
    MISSING_CONTROLLER_IN_AUTOMATION = (42,)
    CONFIGURATION_ERROR = (43,)
    COMMON_AUTOMATION_NOT_AVAILABLE = (44,)

    ILLEGAL_EVENT = (50,)

    ILLEGAL_DEVICE = (51,)

    SERVICE_NOT_SUPPORTED = 60

    EVENT_TOO_LONG = 253
    ILLEGAL_ARGUMENT = 254
    INTERNAL_ERROR = 255


class CCAN_Error(BaseException):
    __codes = {}
    __codes[CCAN_ErrorCode.OK] = "No Error occured"
    __codes[CCAN_ErrorCode.TIME_OUT] = "Controller not reachable"
    __codes[CCAN_ErrorCode.SERVER_NOT_REACHABLE] = (
        "CCAN server is not reachable. Please start a server"
    )
    __codes[CCAN_ErrorCode.DESTINATION_NOT_REACHABLE] = (
        "Destination address is not reachable. Please check the address"
    )
    __codes[CCAN_ErrorCode.BROADCAST_NO_RESPONSE] = (
        "Could not get any response from the CCAN network. NO controllers are available"
    )
    __codes[CCAN_ErrorCode.PROTOCOL_EVENT_INVALID] = (
        "Detected an invalid protocol event"
    )

    __codes[CCAN_ErrorCode.FILE_NOT_FOUND] = "File not found"
    __codes[CCAN_ErrorCode.FILE_INVALID] = "File is invalid"
    __codes[CCAN_ErrorCode.TARGET_UP_TO_DATE] = (
        "Download is not needed. Target is already up to date"
    )
    __codes[CCAN_ErrorCode.FLASH_ERASE_FAILURE] = (
        "Controller noticed an error when erasing FLASH memory prior to the download start."
    )
    __codes[CCAN_ErrorCode.UPDATE_FAILURE] = "Update failed"

    __codes[CCAN_ErrorCode.ILLEGAL_EXPANDER_TYPE] = "Unknown Expander Type"
    __codes[CCAN_ErrorCode.EXPANDER_INITIALIZATION_FAILED] = (
        "Expander could not be initialized"
    )

    __codes[CCAN_ErrorCode.DS1820_NO_SENSOR_DETECTED] = "No sensor detected"
    __codes[CCAN_ErrorCode.DS1820_GND_AND_DATA_ARE_CONNECTED] = (
        "GND and DATA line are connected"
    )
    __codes[CCAN_ErrorCode.DS1820_SENSING_ERROR] = (
        "Address bit sensing error.\n"
        + "->  Pull-up resistor might be not strong enough (lower resistance)\n"
        + "->  or SEARCH_ROM command has not been acknowleged by the device\n"
        + "->  or invalid read timings have been provided (when reading temperature from Dallas sensor)\n"
        +" ->  or no Dallas temperature sensor is connected. Please check for sensor and wiring."
    )
    __codes[CCAN_ErrorCode.DS1820_PIN_NOT_AVAILABLE] = (
        "Pin is not available for sensing. It is already used in the controller configuration"
    )
    __codes[CCAN_ErrorCode.DS1820_PIN_NOT_AVAILABLE] = (
        "Pin is not available for sensing. It is already used in the controller configuration"
    )

    __codes[CCAN_ErrorCode.CONFIGURATION_NOT_AVAILABLE] = (
        "Configuration file has not been loaded. This is needed for this request,"
    )
    __codes[CCAN_ErrorCode.UNEXPECTED_CONTROLLER_NOT_IN_AUTOMATION] = (
        "Detected controller does not belong to the specified automation"
    )
    __codes[CCAN_ErrorCode.MISSING_CONTROLLER_IN_AUTOMATION] = (
        "Controller responses are incomplete"
    )
    __codes[CCAN_ErrorCode.CONFIGURATION_ERROR] = (
        "A general configuration error has been detected"
    )
    __codes[CCAN_ErrorCode.COMMON_AUTOMATION_NOT_AVAILABLE] = (
        "No common automation can be derived"
    )

    __codes[CCAN_ErrorCode.ILLEGAL_EVENT] = (
        "Error during evaluation of event. Either the event is not well formed or the used automation file does not fit"
    )

    __codes[CCAN_ErrorCode.ILLEGAL_DEVICE] = "Device is not defined."

    __codes[CCAN_ErrorCode.SERVICE_NOT_SUPPORTED] = "Service not supported"

    __codes[CCAN_ErrorCode.DEGRADATION_STATUS_NOT_RESOLVABLE] = (
        "Internal error: could not interpret controller feedback"
    )

    __codes[CCAN_ErrorCode.EVENT_TOO_LONG] = (
        "Event exceeds the maximum length of an event. Action aborted"
    )
    __codes[CCAN_ErrorCode.ILLEGAL_ARGUMENT] = "Illegal argument used"
    __codes[CCAN_ErrorCode.INTERNAL_ERROR] = "Internal Error. Please check"

    def __init__(self, my_error_code, my_explanation_text=None):
        if my_error_code in CCAN_ErrorCode:
            self.__code = my_error_code
            self.__explanation_text = my_explanation_text
            return
        raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ERROR_CODE)

    def __str__(self):
        if self.__explanation_text is None:
            return str(CCAN_Error.__codes[self.__code] + ".")
        return str(CCAN_Error.__codes[self.__code]) + ". " + self.__explanation_text

    def get_code(self):
        return self.__code
