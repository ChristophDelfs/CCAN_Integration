import sys
import argparse
import socket
import time

# CCAN:
from src.base.PlatformDefaults import PlatformDefaults

#
# USED INTERACTIONS:
#

# controller interactions:
from src.cli.interactions.controller.Ping import Ping
from src.cli.interactions.controller.Ping  import Interaction
from src.cli.interactions.controller.Memory import Memory
from src.cli.interactions.controller.ProcessorLoad import ProcessorLoad
from src.cli.interactions.controller.BoardInfo import BoardInfo
from src.cli.interactions.controller.SetBoardLED import SetBoardLED
from src.cli.interactions.controller.SwID import SwID
from src.cli.interactions.controller.Lock import Lock
from src.cli.interactions.controller.Reset import Reset
from src.cli.interactions.controller.ConfigurationInformation import ConfigurationInformation
from src.cli.interactions.controller.Version import Version
from src.cli.interactions.controller.Update import Update
from src.cli.interactions.controller.EnableVerboseEvents import EnableVerboseEvents
from src.cli.interactions.controller.DisableVerboseEvents import DisableVerboseEvents
from src.cli.interactions.controller.UpdateFirmware import UpdateFirmware
from src.cli.interactions.controller.UpdateBootloader import UpdateBootloader
from src.cli.interactions.controller.WriteFirmware import WriteFirmware
from src.cli.interactions.controller.EnableApplicationEventsOnly import EnableApplicationEventsOnly
from src.cli.interactions.controller.DisableApplicationEventsOnly import DisableApplicationEventsOnly
from src.cli.interactions.controller.DetectDS1820 import DetectDS1820
from src.cli.interactions.controller.DetectExpander import DetectExpander
from src.cli.interactions.controller.InitializeExpander import InitializeExpander
from src.cli.interactions.controller.EraseConfiguration import EraseConfiguration
from src.cli.interactions.controller.ProcessorLoad import ProcessorLoad
from src.cli.interactions.controller.DS1820SetReadTimings import DS1820SetReadTimings
from src.cli.interactions.controller.DS1820RequestMeasurement import DS1820RequestMeasurement
from src.cli.interactions.controller.DS1820ReadMeasurement import DS1820ReadMeasurement
from src.cli.interactions.controller.GetEngineThreadFailures import GetEngineThreadFailures
from src.cli.interactions.controller.UpTime import UpTime
from src.cli.interactions.controller.DebugEvenTestt import DebugEventTest

# broadcast interactions:
from src.cli.interactions.broadcast.BroadcastPing import BroadcastPing
from src.cli.interactions.broadcast.BroadcastBoardInfo import BroadcastBoardInfo
from src.cli.interactions.broadcast.BroadcastReset import BroadcastReset
from src.cli.interactions.broadcast.BroadcastLock import BroadcastLock
from src.cli.interactions.broadcast.BroadcastConfigurationInformation import BroadcastConfigurationInformation
from src.cli.interactions.broadcast.BroadcastSwID import BroadcastSwID
from src.cli.interactions.broadcast.BroadcastVersion import BroadcastVersion
from src.cli.interactions.broadcast.BroadcastMemory import BroadcastMemory
from src.cli.interactions.broadcast.BroadcastEnableVerboseEvents import BroadcastEnableVerboseEvents
from src.cli.interactions.broadcast.BroadcastDisableVerboseEvents import BroadcastDisableVerboseEvents
from src.cli.interactions.broadcast.BroadcastUpdateFirmware import BroadcastUpdateFirmware
from src.cli.interactions.broadcast.BroadcastEnableApplicationEventsOnly import BroadcastEnableApplicationEventsOnly
from src.cli.interactions.broadcast.BroadcastDisableApplicationEventsOnly import BroadcastDisableApplicationEventsOnly
from src.cli.interactions.broadcast.BroadcastEraseConfiguration import BroadcastEraseConfiguration
from src.cli.interactions.broadcast.BroadcastProcessorLoad import BroadcastProcessorLoad
from src.cli.interactions.broadcast.BroadcastEngineThreadFailures import BroadcastEngineThreadFailures
from src.cli.interactions.broadcast.BroadcastUptime import BroadcastUptime

# automation interactions:
from src.cli.interactions.automation.AutomationPing import AutomationPing
from src.cli.interactions.automation.AutomationCreateLog import AutomationCreateLog
from src.cli.interactions.automation.AutomationReadLog import AutomationReadLog
from src.cli.interactions.automation.AutomationBoardInfo import AutomationBoardInfo
from src.cli.interactions.automation.AutomationLock import AutomationLock
from src.cli.interactions.automation.AutomationReset import AutomationReset
from src.cli.interactions.automation.AutomationConfigurationInformation import AutomationConfigurationInformation
from src.cli.interactions.automation.AutomationDump import AutomationDump
from src.cli.interactions.automation.AutomationSwID import AutomationSwID
from src.cli.interactions.automation.AutomationVersion import AutomationVersion
from src.cli.interactions.automation.AutomationMemory import AutomationMemory
from src.cli.interactions.automation.AutomationEnableVerboseEvents import AutomationEnableVerboseEvents
from src.cli.interactions.automation.AutomationDisableVerboseEvents import AutomationDisableVerboseEvents
from src.cli.interactions.automation.AutomationEraseConfiguration import AutomationEraseConfiguration
from src.cli.interactions.automation.AutomationGetVariable import AutomationGetVariable
from src.cli.interactions.automation.AutomationSetVariable import AutomationSetVariable
from src.cli.interactions.automation.AutomationSendEvent import AutomationSendEvent
from src.cli.interactions.automation.AutomationDegradationStatus import AutomationDegradationStatus
from src.cli.interactions.automation.AutomationProcessorLoad import AutomationProcessorLoad
from src.cli.interactions.automation.AutomationUpdate import AutomationUpdate
from src.cli.interactions.automation.AutomationUptime import AutomationtUptime
from src.cli.interactions.automation.AutomationEngineThreadFailures import AutomationEngineThreadFailures

# additional imports:
from src.base.PlatformConfiguration import PlatformConfiguration
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error

from src.connect.Connector import Connector


class IP_AddressRange:
    def __init__(self):
        pass

    def __call__(self, my_symbolic_address):
        try:
            resolved_address = socket.gethostbyname(my_symbolic_address)           
            #value = socket.getaddrinfo(my_ip_address,0)[0][4][0]
        except Exception:
            
            raise  argparse.ArgumentTypeError(f"Argument {my_symbolic_address} is not a valid IP address.") 
        return resolved_address

class PortRange:
    def __init__(self):
        self.__platform_configuration = PlatformConfiguration().get()
        self.__min = self.__platform_configuration["UDP_SERVER"]["MIN_PORT"]
        self.__max = self.__platform_configuration["UDP_SERVER"]["MAX_PORT"]      
        self.__filename = self.__platform_configuration["PlatformConfigurationFile"]

    def __call__(self, my_port):
        try:
            value = int(my_port)
        except ValueError:
            raise  argparse.ArgumentTypeError(f"Port values must be integers in the range [{self.__min}, {self.__max}]. Please check also {self.__filename}.")
        
        if value < self.__min or value > self.__max:
           raise  argparse.ArgumentTypeError(f"Port values must be integers in the range [{self.__min}, {self.__max}]. Please check also {self.__filename}.")
       
        return value

class CLI():
    def print_help(self):
        
        self.__main_parser.print_help()
       
        subparsers_actions = [
            action for action in [self.__subparsers]
            if isinstance(action, argparse._SubParsersAction)]

        for subparsers_action in  subparsers_actions:
            # get all subparsers and print help            
            old_subparser = None
            for choice, subparser in subparsers_action.choices.items():                             
                if old_subparser is not subparser:
                    print(subparser.format_help())
                    old_subparser = subparser
        return

    def __init__(self):
        
        # read user specific configuration:
        self._platform_configuration = PlatformConfiguration().get()

        #
        # create parser:
        #

        connect_server_ip_address = self._platform_configuration["CONNECTION_SERVER"]["IP_ADDRESS"]

     
        self.__main_parser = self.create_top_level_parser(connect_server_ip_address)              
        subparsers = self.__main_parser.add_subparsers(dest = "addressing")       
        # add subparsers:
        self.add_automation_parser(subparsers)       
        self.add_broadcast_parser(subparsers)    
        self.add_controller_parser(subparsers)   

        #
        # 
        #  help printing 
        #

        # preserve for help prints:
        self.__subparsers = subparsers
 
        if len(sys.argv) == 1:
            # no arguments passed, print help:
            self.print_help() 
            quit()

        args = self.__main_parser.parse_args()       
        arguments = vars(args)

        if '--help' in sys.argv:
            self.print_help()          
            return
      
        try:
            self.__do(arguments)
        except CCAN_Error as ex:
            print(ex)            
            exit()

      

    def create_top_level_parser(self, connect_server_ip_address):
        parser = argparse.ArgumentParser(prog="ccan_cli",description='CCAN command line interface', add_help = False, formatter_class=argparse.RawTextHelpFormatter)
    
        parser.add_argument("--ip_address", type = IP_AddressRange(), metavar='address', help = "states the ip address of the CCAN server (default: " + connect_server_ip_address + ")",default= connect_server_ip_address)
        parser.add_argument("--verbose", help= "add additional output",action ='store_true')     
        parser.add_argument("--port", type= PortRange(), help = "state the port of the CCAN server. If not provided, ccan_cli will scan for an available CCAN server.",default = PlatformDefaults.INVALID_SERVER_PORT)        
        parser.add_argument('-h', '--help',action="store_const", const = "lock", default=argparse.SUPPRESS, help='Show this help message and exit.')        
        return parser

    def add_automation_parser(self, my_subparser):
        parser = my_subparser.add_parser("a", aliases = ["auto"], help="connect to all controllers in the CCAN bus using the automation configuration.")     
        parser.add_argument("configuration",help="optional: configuration file",nargs='?', type=str, metavar = "configuration_file", default = False)
        group = parser.add_mutually_exclusive_group(required=True)
        self.add_common_arguments(group)     
        self.add_automation_arguments(group)
        return parser

    def add_broadcast_parser(self, my_subparser):
        parser = my_subparser.add_parser("b",aliases = ["broadcast"], help="connect to all controllers in the CCAN bus")    
        group = parser.add_mutually_exclusive_group(required=True)
        self.add_common_arguments(group)
        self.add_broadcast_arguments(group)
        return parser

    def add_controller_parser(self, my_parser):
        parser = my_parser.add_parser("c", aliases = ["controller"], help="connects to a selected controller")     
        parser.add_argument("address",help="controller address", type=int)
        group = parser.add_mutually_exclusive_group(required=True)
        self.add_common_arguments(group)
        self.add_controller_arguments(group)
        return parser 

    def add_common_arguments(self,group):
        group.add_argument("-p","--ping",help="pings controller and measures response times and counts losses. Stop with Ctrl-C.",action="store_const", const = "ping")
        group.add_argument("-b","--board_info", help="get controller type and UUID",action="store_const", const = "board_info") 
        group.add_argument("-r","--reset", help="resets controller", action="store_const", const = "reset")  
        group.add_argument("-l","--lock", help="locks controller if controller is in bootloader mode",action="store_const", const = "lock")    
        group.add_argument("-c","--configuration_info", help="get info on controller configuration ",action="store_const", const = "configuration_info")
        group.add_argument("-i","--sw_id",help="get info whether controller runs 'Bootloader' or 'Firmware'", action="store_const", const = "sw_id")
        group.add_argument("-v","--version",help="get version of running SW and used configuration",action="store_const", const = "version")
        group.add_argument("-m","--memory", help="get the used and free RAM space on device",action="store_const", const = "memory")
        group.add_argument("--load", help="provide processor usage and idle information",action="store_const", const = "load")
        group.add_argument("--enable_verbose_events",help="controller engine sets event verbosity. All events are shipped.",action="store_const", const = "enable_verbose_events")
        group.add_argument("--disable_verbose_events",help="controller engine sets event verbosity. Only necessary events are shipped (default).",action="store_const", const = "disable_verbose_events")
        group.add_argument("--enable_application_events_only",help="controller engine sets event verbosity. All events are shipped.",action="store_const", const = "enable_application_events_only")
        group.add_argument("--disable_application_events_only",help="controller engine sets event verbosity. Only necessary events are shipped (default).",action="store_const", const = "disable_application_events_only")  
        group.add_argument("--engine_thread_failures",help="Development information: retrieve the number of thread activations which did not terminate as planned.",action="store_const", const = "engine_thread_failures")  
        group.add_argument("--uptime",help="get elapsed time since start of the SW",action="store_const", const = "uptime")        
        group.add_argument("--debug_event_test",metavar='repetitions', type=int, help="triggers that the controller creates a short burst of test events")   
  
    def add_automation_arguments(self, my_group):      
        my_group.add_argument("-d","--dump" ,nargs='?',type= str, metavar='filter', help="dump events from CCAN bus in colors",action="store", const = "")
        my_group.add_argument("--get_variable",type= str, metavar= 'name', help="get the value of a device variable from the used automation which is described via its name (format: device_name::variable_name).")
        my_group.add_argument("--set_variable", nargs= 2, metavar=('name','value'), help="set the value of a device variable which is described via its name (format: device_name::variable_name)")
        my_group.add_argument("--send_event",type=str,metavar= 'event with parameters', help="sends an event to the automation.")
        my_group.add_argument("--degradation_status",help="show degradation status for all elements of the automation",action="store_const", const = "degradation_status")
        my_group.add_argument("--update", nargs='?',type= str, metavar='filename', help ="update current configuration to all controllers of the automation, but only if data is not up to date", const= '')
        my_group.add_argument("--create_log",  nargs='?', metavar='log_file', type= str, help="creates a log file which stores all received events", const = False)
        my_group.add_argument("--read_log",nargs='?', metavar='log_file', type= str, help="creates a log file which stores all received events", const =  False)
    
    def add_broadcast_arguments(self, my_group):      
        my_group.add_argument("--update_firmware",help="updates firmware of all controllers in the network",action="store_const", const = "update_firmware")

    def add_controller_arguments(self, my_group):
        my_group.add_argument("--detect_ds1820", metavar='pin', type= int, help="detect connected DS18x20 circuits connected to the given pin of the controller board (if supported by the board).")
        my_group.add_argument("--ds1820_set_read_timings",nargs = 4, metavar=('read_pulldown_period','floating_period_before_sampling','floating_period_after_sampling','recovery_period'), help = "Set the he following timings in µs:  <read_pulldown_period>, <floating_period_before_sampling>,\
                              <floating_period_after_sampling>,<recovery_period>. Provide value 0 for any timing if you want to apply the default timings [1,10,50,1].")
        my_group.add_argument("--ds1820_trigger_measurement", nargs = 2, metavar=('pin','romcode'), help= "Triggers temperaturement in DS18x20 sensor. You need to provide pin [0..3] and ROM code of the sensor as provided by the detection")
        my_group.add_argument("--ds1820_read_measurement", nargs = 2, metavar=('pin','romcode'), help= "Reads out temperature which has been measured / converted in a DS18x20 sensor beforehand. You need to provide pin [0..3] and the ROM code of the sensor as provided by the detection.")
        my_group.add_argument("--detect_expander",help="detect connected expander devices connected to the controller board if supported by the board.",action="store_const", const = "detect_expander")
        my_group.add_argument("--initialize_expander", nargs=3 ,metavar =('address','name','"expander type"'), help="initializes EEPROM for an Expander32 [address] [name] [expander_type]. expander_type is one value from [Input,Output]")        
        my_group.add_argument("-u","--update",metavar='filename', type=str,help ="update named configuration or firmware to an embedded controller, but only if data is not up to date")
        my_group.add_argument("--write",metavar='filename', type=str,help ="write named configuration or firmware to an embedded controller")        
        my_group.add_argument("--update_firmware", help ="updates controller with most recent firmware release SW if needed.", action="store_const", const = "update_firmware")
        my_group.add_argument("--update_bootloader", help ="updates controller with most recent bootloader release SW if needed.", action="store_const", const = "update_bootloader")
        my_group.add_argument("--write_firmware", help ="(re)writes controller with most recent release SW.", action="store_const", const = "write_firmware")
        my_group.add_argument("--set_board_led", nargs= 2, metavar=('led_id','led_state'),  help="allows to set the state of board LED's 'ALARM' and 'WARN' to one value out of 'ON','FLASHING' or 'OFF'", action= "store")
        my_group.add_argument("--erase_configuration",help ="erase controller configuration ", action="store_const", const = "erase_configuration")
    #
    #
    #   
    #
    #
    #

    def get_create_log_file(self, my_actions):        
        filename = my_actions["create_log"]         
        return [Interaction.ENDLESS_RETRIES, filename] 

    def get_read_log_file(self, my_actions):         
        filename = my_actions["read_log"]   
        return [0, filename] 

    def get_update_parameters(self, my_actions):         
        try:
            filename = my_actions["update"]      
        except KeyError:
            filename = None
        return [1, filename, False]

    def get_write_parameters(self, my_actions):        
        return [1, my_actions["write"], True]    
    
    def get_dump_filter(self, my_actions):
          filter = my_actions["dump"]
          return [Interaction.ENDLESS_RETRIES, filter]

    def get_send_event_parameters(self, my_actions):        
        return [1, my_actions["send_event"]]        

    def get_board_led_parameters(self,my_actions):
        return [1,  my_actions["set_board_led"][0],  my_actions["set_board_led"][1]]

    def get_ds1820_parameters(self,my_actions):
        return [1, my_actions["detect_ds1820"]]
        
    def get_ds1820_trigger_measurement(self,my_actions):
        pin =  my_actions["ds1820_trigger_measurement"][0]
        romcode =  my_actions["ds1820_trigger_measurement"][1]
        return [1, pin, romcode]

    def get_ds1820_read_measurement(self,my_actions):
        pin =  my_actions["ds1820_read_measurement"][0]
        romcode =  my_actions["ds1820_read_measurement"][1]
       
        return [1, pin, romcode]

    def get_ds1820_set_read_timings(self,my_actions):
        pulldown_period = my_actions["ds1820_set_read_timings"][0]
        floating_period_before_sampling =  my_actions["ds1820_set_read_timings"][1]
        floating_period_after_sampling =  my_actions["ds1820_set_read_timings"][2]
        recovery_period =  my_actions["ds1820_set_read_timings"][3]     
       
        return [1, pulldown_period, floating_period_before_sampling, floating_period_after_sampling, recovery_period]

    def get_get_variable_parameter(self,my_actions):
        return [1, my_actions["get_variable"]]
    
    def get_set_variable_parameter(self,my_actions):
        return [1, my_actions["set_variable"][0], my_actions["set_variable"][1]]

    def get_repetition_parameter(self,my_actions):
        return [1, my_actions["debug_event_test"]]


    def get_expander_init_parameters(self,my_actions):
        address = int(my_actions["initialize_expander"][0])
        expander_type = my_actions["initialize_expander"][1]
        expander_name = my_actions["initialize_expander"][2]
        return [1, address,expander_type, expander_name]

    def get_action(self, my_addressing, my_actions):
        action_selected = None
        # determine which action has been selected:
        for key, value in my_actions.items():
            if key == my_actions[key]:
                action_selected = key

        if action_selected is not None:
            return action_selected

        if my_addressing == "controller":           
            if my_actions["update"] is not None:
               return "update"
            
            if my_actions["write"] is not None:
               return "write"

            if my_actions["set_board_led"] is not None:
                return "set_board_led"
            
            if my_actions["detect_ds1820"] is not None:
                return "detect_ds1820"
            
            if my_actions["ds1820_trigger_measurement"] is not None:
                return "ds1820_trigger_measurement"
            
            if my_actions["ds1820_read_measurement"] is not None:
                return "ds1820_read_measurement"

            if my_actions["ds1820_set_read_timings"] is not None:
                return "ds1820_set_read_timings"

            if my_actions["initialize_expander"] is not None:
                return "initialize_expander"      

            if my_actions["debug_event_test"] is not None:
                return "debug_event_test"      
            
        if my_addressing == "automation":            
            if my_actions["set_variable"] is not None:
                return "set_variable"               

            if my_actions["get_variable"] is not None:
                return "get_variable"  
            
            if my_actions["send_event"] is not None:
                return "send_event"  
            
            if my_actions["update"] is not None:
               return "update"            

            if my_actions["dump"] is not None:
               return "dump"     

            if my_actions["create_log"] is not None:
               return "create_log"  
            
            if my_actions["read_log"] is not None:
               return "read_log"  


        raise ValueError

    def __do(self, my_actions):

        # init report level:
        verbosity = my_actions["verbose"]
        Report.push_level(ReportLevel.WARN)
       
        # open connector:
        server_ip_address = my_actions["ip_address"]
        server_port       = my_actions["port"]         
        
        connector = Connector(server_ip_address, server_port)


        # connect to CCAN Server
        result = False
        attempt = 5
        while not result and attempt > 0:
            result = connector.connect()
            time.sleep(0.1)
            attempt -=1
        if not result:
             Report.print(ReportLevel.ERROR,"could not reach CCAN server ..bailing out.\n")
             return False
        connector.stay_connected()

        # how to address the CCAN bus:
        addressing = my_actions["addressing"]
        if addressing.startswith("a"):
            addressing = "automation"
        elif addressing.startswith("b"):
            addressing  = "broadcast"
        else:
            addressing = "controller"


        del my_actions['ip_address'] 
        del my_actions['port']
        del my_actions['verbose']
        del my_actions['addressing']

        action_selected = self.get_action(addressing, my_actions)

        # create action table:
        interactions = {   
            "board_info"            : { "automation": AutomationBoardInfo, "broadcast" : BroadcastBoardInfo, "controller": BoardInfo , "parameter": [1],  "ReportLevel": ReportLevel.VERBOSE },
            "ping"                  : { "automation": AutomationPing, "broadcast" : BroadcastPing, "controller": Ping , "parameter": [Interaction.ENDLESS_RETRIES, 0.1 ] , "ReportLevel": ReportLevel.VERBOSE },
            "configuration_info"    : { "automation": AutomationConfigurationInformation,"broadcast": BroadcastConfigurationInformation, "controller": ConfigurationInformation, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE } ,          
            "reset"                 : { "automation": AutomationReset, "broadcast": BroadcastReset, "controller": Reset, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },  
            "lock"                  : { "automation": AutomationLock, "broadcast": BroadcastLock, "controller": Lock, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },
            "dump"                  : { "automation": AutomationDump, "parameter" : self.get_dump_filter , "ReportLevel": ReportLevel.VERBOSE},
            "create_log"            : { "automation": AutomationCreateLog, "parameter": self.get_create_log_file ,"ReportLevel": ReportLevel.VERBOSE},
            "read_log"              : { "automation": AutomationReadLog, "parameter": self.get_read_log_file ,"ReportLevel": ReportLevel.VERBOSE},
            "get_variable"          : { "automation": AutomationGetVariable, "parameter" : self.get_get_variable_parameter, "ReportLevel": ReportLevel.VERBOSE},
            "set_variable"          : { "automation": AutomationSetVariable, "parameter" : self.get_set_variable_parameter, "ReportLevel": ReportLevel.VERBOSE},            
            "sw_id"                 : { "automation": AutomationSwID, "broadcast": BroadcastSwID, "controller": SwID, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },
            "version"               : { "automation": AutomationVersion, "broadcast": BroadcastVersion, "controller": Version, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },            
            "load"                :   { "automation": AutomationProcessorLoad, "broadcast": BroadcastProcessorLoad, "controller": ProcessorLoad, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },   
            "memory"                : { "automation": AutomationMemory, "broadcast": BroadcastMemory, "controller": Memory, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },    
            "enable_verbose_events" : { "automation": AutomationEnableVerboseEvents, "broadcast": BroadcastEnableVerboseEvents, "controller": EnableVerboseEvents, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },    
            "disable_verbose_events": { "automation": AutomationDisableVerboseEvents, "broadcast": BroadcastDisableVerboseEvents, "controller": DisableVerboseEvents, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },    
            "enable_application_events_only" : { "automation": AutomationEnableVerboseEvents, "broadcast": BroadcastEnableApplicationEventsOnly, "controller": EnableApplicationEventsOnly, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },    
            "disable_application_events_only": { "automation": AutomationDisableVerboseEvents, "broadcast": BroadcastDisableApplicationEventsOnly, "controller": DisableApplicationEventsOnly, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },    
            "update"                : { "automation": AutomationUpdate, "controller": Update, "parameter": self.get_update_parameters , "ReportLevel": ReportLevel.VERBOSE },     
            "write"                 : { "controller": Update, "parameter": self.get_write_parameters , "ReportLevel": ReportLevel.VERBOSE },     
            "send_event"            : { "automation": AutomationSendEvent, "parameter": self.get_send_event_parameters , "ReportLevel": ReportLevel.VERBOSE },                             
            "set_board_led"         : { "controller": SetBoardLED, "parameter": self.get_board_led_parameters , "ReportLevel": ReportLevel.VERBOSE },       
            "ds1820_set_read_timings" : { "controller": DS1820SetReadTimings, "parameter": self.get_ds1820_set_read_timings, "ReportLevel": ReportLevel.VERBOSE },       
            "detect_ds1820"         : { "controller": DetectDS1820, "parameter": self.get_ds1820_parameters , "ReportLevel": ReportLevel.VERBOSE },       
            "ds1820_trigger_measurement" : { "controller": DS1820RequestMeasurement, "parameter": self.get_ds1820_trigger_measurement , "ReportLevel": ReportLevel.VERBOSE },       
            "ds1820_read_measurement" : { "controller": DS1820ReadMeasurement, "parameter": self.get_ds1820_read_measurement , "ReportLevel": ReportLevel.VERBOSE },             
            "detect_expander"       : { "controller": DetectExpander, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },  
            "degradation_status"    : { "automation": AutomationDegradationStatus,"parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },
            "initialize_expander"   : { "controller": InitializeExpander, "parameter": self.get_expander_init_parameters , "ReportLevel": ReportLevel.VERBOSE },  
            "update_firmware"       : { "controller": UpdateFirmware, "broadcast": BroadcastUpdateFirmware, "parameter": [1], "ReportLevel": ReportLevel.VERBOSE },     
            "update_bootloader"     : { "controller": UpdateBootloader,"parameter": [1], "ReportLevel": ReportLevel.VERBOSE },                 
            "write_firmware"        : { "controller": WriteFirmware,"parameter": [1], "ReportLevel": ReportLevel.VERBOSE },   
            "uptime"                : { "automation": AutomationtUptime,"broadcast" : BroadcastUptime, "controller": UpTime, "parameter":[1], "ReportLevel": ReportLevel.VERBOSE }, 
            "erase_configuration"   : { "controller": EraseConfiguration, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE },  # "automation": AutomationEraseConfiguration,"broadcast": BroadcastEraseConfiguration,
            "engine_thread_failures": { "automation":  AutomationEngineThreadFailures, "broadcast":  BroadcastEngineThreadFailures, "controller": GetEngineThreadFailures, "parameter": [1] , "ReportLevel": ReportLevel.VERBOSE},

            "debug_event_test"      : { "controller": DebugEventTest, "parameter": self.get_repetition_parameter , "ReportLevel": ReportLevel.VERBOSE },   

        }

        # interaction:
        interaction = interactions[action_selected][addressing]
        # interaction default parameter:
        parameter   = interactions[action_selected]["parameter"]

        if callable(parameter):
            parameter = parameter(my_actions)

        # set destination address if applicable:
        if addressing == "controller":
            connector.set_destination_address(my_actions["address"])
            parameter = [ connector] + parameter
        else:
        # set waiting time for answers in case of a broadcast:
            waiting_time = self._platform_configuration["RESPONSE_WAITING_TIME"]
            if action_selected == "ping":
                waiting_time = 0.05
            parameter = [ connector] + [waiting_time] + parameter  
       

        if addressing == "automation":
            parameter += [my_actions["configuration"]]        
        
        interaction_reportlevel = interactions[action_selected]["ReportLevel"]

        Report.pop_level()
        if verbosity:
            Report.push_level(ReportLevel.VERBOSE)
        else:
            Report.push_level(interaction_reportlevel)
        try:
            interaction(*parameter).do()
        except CCAN_Error as error:            
            Report.print(ReportLevel.ERROR,str(error) + "\n")

        connector.disconnect()

        Report.pop_level()
