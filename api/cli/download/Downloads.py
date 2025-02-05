import os
import binascii
from pathlib import Path
import abc


from src.base.CCAN_Defaults import CCAN_Defaults
from src.PyCCAN_Writer import Writer
from src.PyCCAN_ConvertBinary import SequenceExtractor, SequenceCreator
from src.PyCCAN_Writer import Writer
from src.PyCCAN_ConvertBinary import SequenceCreator
from intelhex import IntelHex
from src.base.CCAN_Defaults import CCAN_Defaults
from src.base.PlatformDefaults import PlatformDefaults
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode


class DownloadItem(metaclass=abc.ABCMeta):
    def __init__(self,my_filename):

        file = Path(my_filename)
        if file.is_file() == False:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"File <"+ my_filename+"> does not exist - bailing out")

        self._valid = False
        
        self._controller_type  = None
        self._controller_crc   = None     
        self._file_type        = None
        self._dl               = None  
        self._file_crc         = None   
        self._version          = None
        self._filename         = my_filename     

        self._load_file()
        self._set_attributes()              

    @abc.abstractmethod        
    def _set_attributes(self):
        raise NotImplementedError  

    @abc.abstractmethod        
    def _load_file(self):
        raise NotImplementedError 

    def is_valid(self):
        return self._valid

    def get_file_modification_date(self):
        return self._file_modification_date

    def get_file_type(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)            
        return self._file_type
        
    def get_controller_crc(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)
        return self._controller_crc & 0xffffffff # remove trailer       

    def get_controller_type(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)              
        # remove start and end:
        return self._controller_type
           
    def get_file_data(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)
        return self._dl
        
    def get_file_crc(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)       
        return self._file_crc    
       
    def get_file_version(self):
        if self._valid is False:
            raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)       
        return self._file_version        


class DownloadImage(DownloadItem):
    def __init__(self, my_filename):
        super().__init__(my_filename)       

    def abstractmethod(self):
        return 0

    def _load_file(self):
        if self._filename.endswith(".hex"):
            dl_intel = IntelHex()
            dl_intel.loadhex(self._filename)    
            self._segments = dl_intel.segments()        
            self._dl = []

            for segment in self._segments:
                for i in range(segment[0], segment[1]):
                    self._dl.append(dl_intel[i])   

    def _set_attributes(self):
        if self._dl == None:          
            return
        
        ccan_defaults = CCAN_Defaults()
        default_file = os.sep.join([os.environ["CCAN"],"gen","ccan_generated_definitions"])
        ccan_defaults.init_from_pkl(default_file)
        controller_map = ccan_defaults.get_map("CONTROLLER_CRC_LIST")
        
        # check for known image:
        result = None
        for element in controller_map:
            crc = controller_map[element]
            seq = SequenceCreator()
            seq.convert64(crc)
            crc_dl = seq.get_sequence()
            found = subfinder(self._dl,crc_dl)

            if len(found) == 1:
                if result is None:
                    result = element                  
                else:
                    # ambigous, this shall happen, if hex file is an updater image
                    # in this case both crcs, bootloader and updater crc, are embedded.
                    if result.endswith("BOOTLOADER"):
                        if element.endswith("UPDATER"):
                            result = element
                    else:
                        if not element.endswith("UPDATER"):
                            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"File <"+ self._filename+"> has apparently multiple descriptions for a target controller SW type.")
        if result == None:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Description for a target controller SW type has not been found in file <" + self._filename + ".")

        self._controller_crc  =  controller_map[result]
        
        for element in ["BOOTLOADER","FIRMWARE","UPDATER"]:
                if result.endswith(element):
                    self._file_type = element
                    break
        if self._file_type is None:
            return

        self._controller_type = result[len("CONTROLLER_CRC_LIST_"):len(result) - len(self._file_type)-1]   
        self._file_crc = binascii.crc32(bytes(self._dl)) 

        version_cookie_start = PlatformDefaults.VERSION_MAGIC_COOKIE_START
        version_cookie_list = []
        for char in version_cookie_start:
            version_cookie_list.append(ord(char))

        # find version information:
        index = index_finder(version_cookie_list,self._dl)
        if index == None:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"File <"+ self._filename+"> has no version information.")

        # extract version string:
        start_of_version_string = index+len(version_cookie_start)       
        end_of_version_string = self._dl.index(0,index+len(version_cookie_start))
        raw_version = self._dl[start_of_version_string :end_of_version_string]
        version_string = ''.join([chr(entry) for entry in raw_version])
       
        # get modification data:
        self._file_modification_date = int(os.path.getctime(self._filename))

        # extract version information: 
        index_minor = version_string.find('.')
        index_patch = version_string.find('.',index_minor+1)
        major_version = int(version_string[0:index_minor])
        minor_version = int(version_string[index_minor+1:index_patch])
        patch_version = int(version_string[index_patch+1:])

        self._file_version    = [ major_version, minor_version, patch_version]
        self._valid           = True                 

    
    def get_segments(self):
        return self._segments


class DownloadConfiguration(DownloadItem):
    def __init__(self, my_filename):
        super().__init__(my_filename)      

    def _load_file(self):      
        if self._filename.endswith(".bin"):
            with open(self._filename,mode='rb') as file:
                self._dl = file.read()     


    def _set_attributes(self):
        if self._dl == None:          
            return
        
        header = SequenceExtractor(self.__get_section(0))
        self.__magic_cookie   = header.convertback16()
        if self.__magic_cookie != Writer.engine_cookie:
            return        
        self._controller_crc = header.convertback32()

        ccan_defaults = CCAN_Defaults()
        default_file = os.environ["CCAN"]+"/gen/ccan_generated_definitions"
        ccan_defaults.init_from_pkl(default_file)
        controller_map = ccan_defaults.get_map("CONTROLLER_CRC_LIST")
        # check for entry:  
        
        result = None    
        for element in controller_map:
            crc = controller_map[element] & 0xffffffff 
            if crc == self._controller_crc:
                result = element
                break           
        if result == None:
            return 
         
        for element in ["CONFIGURATION"]:
                if result.endswith(element):
                    self._file_type = element
        if self._file_type is None:
            return

        self._controller_type = result[len("CONTROLLER_CRC_LIST_"):len(result) - len(self._file_type)-1]          
        self._file_crc = binascii.crc32(bytes(self._dl)) 

       
        # get modification data:
        self._file_modification_date = int(os.path.getctime(self._filename))

        # extract version information:
        major_version = header.convertback16()
        minor_version = header.convertback16()
        patch_version = header.convertback16()
        self._file_version = (major_version, minor_version, patch_version)



        self._valid = True

    def __get_section(self,my_header_value):        
        data = self._dl
        while True:
            header_value = data[0]
            if header_value == my_header_value:
                # get length:
                length = data[2]*256+data[1]
                return data[3:length+3]
            data = data[length+4:-1]

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