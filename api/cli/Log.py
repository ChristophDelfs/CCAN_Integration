import sys
import argparse
import socket
import struct

from src.cli.interactions.automation.AutomationBase import AutomationBase


''''
log functionality for CCAN

ccan_log

Function automatically connects to the running automation and logs the data.

'''


# CCAN:
from src.base.PlatformDefaults import PlatformDefaults

#
# USED INTERACTIONS:
#


# automation interactions:

from src.cli.interactions.automation.AutomationDump import AutomationDump

# additional imports:
from src.base.PlatformConfiguration import PlatformConfiguration
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error

from src.connect.Connector import Connector


class IP_AddressRange:
    def __init__(self):
        pass

    def __call__(self, my_ip_address):
        try:
            value = socket.getaddrinfo(my_ip_address,0)[0][4][0]
        except Exception:
            raise  argparse.ArgumentTypeError(f"Argument {my_ip_address} is not a valid IP address.") 
        return value

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

class Log():
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

     
        self.__main_parser = self.create_top_level_parser()              
     
        # 
        #  help printing 
        #

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

      

    def create_top_level_parser(self):
        parser = argparse.ArgumentParser(prog="ccan_cli",description='CCAN command line interface', add_help = True)
    
        parser.add_argument("--ip_address", type = IP_AddressRange(), metavar='address', help = "states the ip address of the CCAN server (default: localhost)",default= "localhost")
        parser.add_argument("--verbose", help= "add additional output",action ='store_true')     
        parser.add_argument("--port", type= PortRange(), help = "state the port of the CCAN server. If not provided, ccan_cli will scan for an available CCAN server.",default = PlatformDefaults.INVALID_SERVER_PORT)               
        parser.add_argument("--log",help= "log into a file",action ='store_true')    
        parser.add_argument("--rlog",help= "read log from a file",action ='store_true')    
        return parser

    def __do(self, my_actions):

        # init report level:
        verbosity = my_actions["verbose"]
        Report.push_level(ReportLevel.WARN)
       
        # open connector:
        server_ip_address = my_actions["ip_address"]
        server_port       = my_actions["port"]         
        log_action        = my_actions["log"]
        
        self.__connector = Connector(server_ip_address, server_port)

        # connect to CCAN Server
        self.__connector.connect()

        if verbosity == True:
            Report.push_level(ReportLevel.VERBOSE)
      
        try:
            if log_action is True:
                self._automation = AutomationBase(self.__connector, 0.1)
                self.write_log()
            else:
                self.read_log()

        except CCAN_Error as error:            
            Report.print(ReportLevel.ERROR,str(error) + "\n")

        self.__connector.disconnect()

        Report.pop_level()


    def write_log(self):
        '''
        Writes all collected events into a log file.
        Format is:
            <Header>
            <pkl-file>
            <event-list>

        The event list is a list of serialized events. 
        '''
        print("start logging")
        log_file = open('my_ccan.log', 'wb')
        self.__connector._write(log_file)

        


        # add data:      
        value1 = 123
        value2 = 3.14
        binary_data = struct.pack("i", value1) + struct.pack("f", value2)

        print("size 1: " + str(len(struct.pack("i", value1))) + "  size 2: " + str(len(struct.pack("f", value2)) ))

        log_file.write(binary_data)
        log_file.close()

    def read_log(self):
        log_file = open('my_ccan.log', 'rb')
        self.__connector._read(log_file)

        # add data:
        val1 = log_file.read(4)
        val2 = log_file.read(4)
        log_file.close()

        value1  =  struct.unpack('i', val1)[0]
        value2  =  struct.unpack('f', val2)[0]
     
        print(value1, value2)
     


    def persistent_id(self,obj):
        return None
    
    def persistent_load(self,my_id):
        # create raw event from id
        return None
