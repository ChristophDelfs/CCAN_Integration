import binascii
from src.base.CCAN_Defaults import CCAN_Defaults
from src.PyCCAN_Writer import Writer
from src.PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator
import os


class DownloadConfiguration():
    def __init__(self, my_filename):
        self.__valid = False
        if my_filename.endswith(".bin"):
            with open(my_filename,mode='rb') as file:
                self.__dl = file.read()
                size = len(self.__dl) # 'ToDo: size correct?
                self.__check_validity()
        else:
            self.__dl = None         

    def __check_validity(self):
        if self.__dl == None:          
            return False
        
        header = SequenceExtractor(self.__get_section(0))
        self.__magic_cookie   = header.convertback16()
        if self.__magic_cookie != Writer.engine_cookie:
            return False          
        self.__controller_crc = header.convertback32()

        ccan_defaults = CCAN_Defaults()
        default_file = os.environ["CCAN"]+"/gen/ccan_generated_definitions"
        ccan_defaults.init_from_pkl(default_file)
        controller_map = ccan_defaults.get_map("CONTROLLER_CRC_LIST")
        # check for entry:  
        
        result = None    
        for element in controller_map:
            crc = controller_map[element] & 0xffffffff 
            if crc == self.__controller_crc:
                result = element
                break           
        if result == None:
            return False
         
        self.__controller_type = result
        self.__valid = True

    def is_valid(self):
        return self.__valid

    def __get_section(self,my_header_value):        
        data = self.__dl
        while True:
            header_value = data[0]
            if header_value == my_header_value:
                # get length:
                length = data[2]*256+data[1]
                return data[3:length+3]
            data = data[length+4:-1]

 
    def get_controller_crc(self):
        if self.__valid is True:
            return self.__controller_crc
        return None

    def get_controller_type(self):
        if self.__valid is True:
            return self.__controller_type.replace("CONTROLLER_CRC_LIST_","")
        return None  

    def get_data(self):
        if self.__valid is False:
            return None
        return self.__dl
        
    def get_crc(self):
        if self.__valid is False:
            return None
        return binascii.crc32(bytes(self.__dl)) 
    

def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            matches.append(pattern)
    return matches
    