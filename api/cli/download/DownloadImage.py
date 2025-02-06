from api.base.CCAN_Defaults import CCAN_Defaults
from api.PyCCAN_Writer import Writer
from api.PyCCAN_ConvertBinary import SequenceCreator
from intelhex import IntelHex
from api.base.CCAN_Defaults import CCAN_Defaults

import os
import binascii
from pathlib import Path
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DownloadImage():
    def __init__(self, my_filename):
        self.__valid = False
        
        self.__controller_type  = None
        self.__controller_crc   = None     
        self.__type             = None
        self.__dl               = None     

        file = Path(my_filename)
        if file.is_file() == False:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"File <"+my_filename+"> does not exist - bailing out")

        if my_filename.endswith(".hex"):
            dl_intel = IntelHex()
            dl_intel.loadhex(my_filename)            
            
            self.__dl = []
            for index in dl_intel.addresses():
               self.__dl.append(dl_intel[index])
       
            self.__set_validity()
            self.__set_version()         
      
            self._segments = dl_intel.segments()     


    def get_segments(self):
        if self.__valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID) 
        return self._segments

    def get_controller_crc(self):
        if self.__valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)
        return self.__controller_crc & 0xffffffff # remove trailer       

    def get_image_type(self):
        if self.__valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)              
        # remove start and end:
        return self._image_type
           
    def get_controller_type(self):
        return self._controller_type

    def get_data(self):
        if self.__valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)
        return self.__dl
        
    def get_crc(self):
        if self.__valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)       
        return binascii.crc32(bytes(self.__dl))      

    def __set_validity(self):
        if self.__dl == None:          
            return False
        
        ccan_defaults = CCAN_Defaults()
        default_file = os.sep.join([os.environ["CCAN"],"gen","ccan_generated_definitions"])
        ccan_defaults.init_from_pkl(default_file)
        controller_map = ccan_defaults.get_map("CONTROLLER_CRC_LIST")
        
        # check for known image:
        self.__valid = False
        result = None
        for element in controller_map:
            crc = controller_map[element]
            seq = SequenceCreator()
            seq.convert64(crc)
            crc_dl = seq.get_sequence()
            found = subfinder(self.__dl,crc_dl)

            if len(found) == 1:
                if result is None:
                    result = element    
                    self.__valid = True
                    break              
                else:
                    # ambigous, this shall happen, if hex file is an updater image
                    # in this case both crcs, bootloader and updater crc, are embedded.
                    if result.endswith("BOOTLOADER"):
                        if element.endswith("UPDATER"):
                            result = element
                    else:
                        if not element.endswith("UPDATER"):
                            return
        if result == None:
            return

        self.__controller_crc =  controller_map[result]
               
        rindex = result.rindex("_")       
        self._controller_type = result[len("CONTROLLER_CRC_LIST_"):rindex]        
        self._image_type = result[rindex+1:]      
        return

    def __set_version(self):
        if self.__valid is True:
            version_cookie = "VERSION_COOKIE"
            version_cookie_list = []
            for char in version_cookie:
                version_cookie_list.append(ord(char))


            index = index_finder(version_cookie_list,self.__dl)
            if index == None:
                return None
            else:
                print (index)
                pass   

def subfinder(mylist, pattern):
    matches = []
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            matches.append(pattern)
    return matches

def index_finder(subseq, seq):
    i, n, m = -1, len(seq), len(subseq)
    try:
        while True:
            i = seq.index(subseq[0], i + 1, n - m + 1)           
            if subseq == seq[i:i + m]:
               return i
    except ValueError:
        return None


    
