from enum import Enum
class CliErrorCode(Enum):
        OK                 = 0
        TIME_OUT           = 1
        SERVER_NOT_REACHABLE = 2
        DESTINATION_NOT_REACHABLE = 3

        FILE_NOT_FOUND = 4
        FILE_INVALID   = 5
        TARGET_UP_TO_DATE = 6

        ILLEGAL_EXPANDER_TYPE = 10
        EXPANDER_INITIALIZATION_FAILED = 11

        DS1820_NO_SENSOR_DETECTED = 20
        DS1820_GND_AND_DATA_ARE_CONNECTED = 21
        DS1820_SENSING_ERROR = 22
        DS1820_PIN_NOT_AVAILABLE = 23

        DEGRADATION_STATUS_NOT_RESOLVABLE = 30,

        CONFIGURATION_NOT_AVAILABLE = 40,
        UNEXPECTED_CONTROLLER_NOT_IN_AUTOMATION = 41,
        MISSING_CONTROLLER_IN_AUTOMATION = 42,

        ILLEGAL_EVENT = 50,

        SERVICE_NOT_SUPPORTED = 60

        EVENT_TOO_LONG   = 253
        ILLEGAL_ARGUMENT = 254    
        INTERNAL_ERROR   = 255


    
class CliError(BaseException):
    __codes = {}
    __codes[CliErrorCode.OK]       = "No Error occured"
    __codes[CliErrorCode.TIME_OUT] = "Controller is not reachable"
    __codes[CliErrorCode.SERVER_NOT_REACHABLE] = "CCAN server is not reachable. Please start a server"
    __codes[CliErrorCode.DESTINATION_NOT_REACHABLE] = "Destination address is not reachable. Please check the address"
 
    __codes[CliErrorCode.FILE_NOT_FOUND] = "File not found"
    __codes[CliErrorCode.FILE_INVALID]   = "File is invalid"
    __codes[CliErrorCode.TARGET_UP_TO_DATE] = "Download is not needed. Target is already up to date"

    __codes[CliErrorCode.ILLEGAL_EXPANDER_TYPE] = "Unknown Expander Type"
    __codes[CliErrorCode.EXPANDER_INITIALIZATION_FAILED] = "Expander could not be initialized"

    __codes[CliErrorCode.DS1820_NO_SENSOR_DETECTED] = "No sensor detected"
    __codes[CliErrorCode.DS1820_GND_AND_DATA_ARE_CONNECTED] = "GND and DATA line are connected"
    __codes[CliErrorCode.DS1820_SENSING_ERROR] = "Address bit sensing error.\n"+ "->  Pull-up resistor might be not strong enough (lower resistance).\n" + "->  or SEARCH_ROM command has not been acknowleged by the device"
    __codes[CliErrorCode.DS1820_PIN_NOT_AVAILABLE] = "Pin is not available for sensing. It is already used in the controller configuration"
    __codes[CliErrorCode.DS1820_PIN_NOT_AVAILABLE] = "Pin is not available for sensing. It is already used in the controller configuration"

    __codes[CliErrorCode.CONFIGURATION_NOT_AVAILABLE] = "Configuration file has not been loaded. This is needed for this request,"
    __codes[CliErrorCode.UNEXPECTED_CONTROLLER_NOT_IN_AUTOMATION] = "Detected controller does not belong to the specified automation"
    __codes[CliErrorCode.MISSING_CONTROLLER_IN_AUTOMATION] = "Controller responses are incomplete"

    __codes[CliErrorCode.ILLEGAL_EVENT] = "Error during evaluation of event. Either the event is not well formed or the used automation file does not fit"
    __codes[CliErrorCode.SERVICE_NOT_SUPPORTED] = "Service not supported"

    __codes[CliErrorCode.DEGRADATION_STATUS_NOT_RESOLVABLE] = "Internal error: could not interpret controller feedback"

    __codes[CliErrorCode.EVENT_TOO_LONG]   = "Event exceeds the maximum length of an event. Action aborted"
    __codes[CliErrorCode.ILLEGAL_ARGUMENT] = "Illegal argument used"
    __codes[CliErrorCode.INTERNAL_ERROR]   = "Internal Error. Please check"
 
 
    def __init__(self, my_error_code, my_explanation_text= None):
        if my_error_code in CliErrorCode:
            self.__code = my_error_code
            self.__explanation_text = my_explanation_text
            return
        return CliError(CliErrorCode.ILLEGAL_ERROR_CODE)
               
    def __str__(self):
        if self.__explanation_text is None:
            return str(CliError.__codes[self.__code]+".")
        return  str(CliError.__codes[self.__code]) + ". " + self.__explanation_text
    
    def get_code(self):     
        return self.__code
