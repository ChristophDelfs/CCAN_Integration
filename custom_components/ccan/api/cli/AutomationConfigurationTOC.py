from enum import Enum
import time

class AutomationConfigurationTOC():
    class Type(Enum):
        CONFIGURATION = 0
        BOOTLOADER    = 1
        FIRMWARE      = 2         

    def __init__(self):
        self.__toc = {}

    def create(self,ccan_address):
        self.__toc[ccan_address] = {}

    def insert(self,ccan_address,my_type, my_version, my_date, my_filename):
        self.__toc[ccan_address][my_type] = [my_version, my_date, my_filename]

    def get_addresses(self): 
        return list(self.__toc)
            
    def get_configurations(self):
        configurations = []
        for board_address in self.__toc:
            mini_toc = self.__toc[board_address]
            (version, date, filename) = mini_toc[AutomationConfigurationTOC.Type.CONFIGURATION]
            configurations.append(filename)
        
        return configurations

    def __str__(self):
        text = ''
        for board_address in self.__toc:
            mini_toc = self.__toc[board_address]
            text+="Board with address " + str(board_address)+ ":\n"
            for type in mini_toc:
                (version,date,filename) = mini_toc[type]

                if date != 0:
                    date_string =  str(time.ctime(date))
                else:
                    date_string = "                        "

                version_string = str(version[0])+"." + str(version[1]) + "." + str(version[2])                             
                if date == 0 and type == AutomationConfigurationTOC.Type.CONFIGURATION:
                    text+= version_string + "                               default configuration\n"
                else:
                    text+= version_string + "   " + date_string + "   " +  filename + "\n"
              
        return text
                