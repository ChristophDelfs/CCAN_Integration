import os
import time
import math

from src.base.LocateFile import locateFile
from src.cli.download.DownloadInfo import DownloadInfo
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel
from src.base.TimeDelta import TimeDelta
from src.cli.interactions.controller.Reset import Reset
from src.base.PlatformConfiguration import PlatformConfiguration
import signal

class DownloadRobot():
    def __init__(self, my_connector,my_filename, enforce_flag, lock_flag):
        
        self._connector = my_connector
        self._platform_configuration = PlatformConfiguration().get()
        try:
            self._filename =  locateFile(my_filename, self._platform_configuration["CONFIGURATION_PATH"],True)
        except FileNotFoundError:
            raise CCAN_Error(CCAN_ErrorCode.FILE_NOT_FOUND,"File " + my_filename + " not found on available path configuration.")
        self._enforce_flag = enforce_flag
        self._lock_flag = lock_flag

    def do(self):        
        signal.signal(signal.SIGINT, self.on_interrupt)
        dl_binary = DownloadInfo.get_result(self._filename)
        file_type = dl_binary.get_file_type()
        try:
            download_type = ["FIRMWARE","CONFIGURATION","UPDATER"].index(file_type)
        except ValueError:
            if file_type == "BOOTLOADER":
                raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID,"File " + self._filename + " is a valid bootloader image. But this cannot be flashed directly with this tool. For updating the bootloader use the Updater instead.")
            else:
                raise CCAN_Error(CCAN_ErrorCode.FILE_INVALID)
       

        # report findings:
        Report.print(ReportLevel.VERBOSE,"Detected " + file_type + " for controller type " + dl_binary.get_controller_type() + " with version " + '.'.join([str(elem) for elem in dl_binary.get_file_version()]) + ".\n")
       

        controller_crc = dl_binary.get_controller_crc()              
        dl = dl_binary.get_file_data()       
        major_version,minor_version,patch_version = dl_binary.get_file_version()
        size = len(dl)  
        crc32 = dl_binary.get_file_crc()          

        # add full path:
        if self._filename[0] != os.sep:
            self._filename  = os.sep.join([os.getcwd(), self._filename])
    
        shortened = False     
        # shorten if necessary:
        if len(self._filename) > 100:
            shortened = True
            # first attempt:
            pos = self._filename.find(os.sep.join(["","CCAN",""]))
            if pos >= 0:
                self._filename = self._filename[pos+len(os.sep):]                             
            if len(self._filename) > 100:
                self._filename = os.path.basename(self._filename)       
            if len(self._filename) > 100:
                self._filename="<Filename_too_long_to_be_saved>"
            
        if shortened == True:
            Report.print(ReportLevel.VERBOSE,"Filename had to be shortened to <" + self._filename + ">.\n")
  
        reset =  Reset(self._connector, 1, my_wait_for_startup= True) ###########################################################################

        modification_date = dl_binary.get_file_modification_date()
        
        # prepare messages:
        bootloader_answers = self._connector.resolve_event_list(["DOWNLOAD_SERVICE::DOWNLOAD_ACK()",\
                                                                    "DOWNLOAD_SERVICE::DOWNLOAD_NACK()",\
                                                                    "DOWNLOAD_SERVICE::FILE_TOO_BIG()",\
                                                                    "DOWNLOAD_SERVICE::FILE_INVALID()",\
                                                                    "DOWNLOAD_SERVICE::VERSION_MISMATCH_WITH_FIRMWARE()", \
                                                                    "DOWNLOAD_SERVICE::VERSION_MISMATCH_WITH_BOOTLOADER()"])

        # prepare events:
        ack_events = self._connector.resolve_event_list(["DOWNLOAD_SERVICE::DOWNLOAD_CHUNK_ACK()","DOWNLOAD_SERVICE::DOWNLOAD_CHUNK_NACK()"])
        download_event = self._connector.resolve_event("DOWNLOAD_SERVICE::DOWNLOAD_CHUNK( data = [0])")

        ready_to_rumble_event  = self._connector.resolve_event("DOWNLOAD_SERVICE::DOWNLOAD_READY_TO_RUMBLE()")
        flash_erase_failure_event =  self._connector.resolve_event("DOWNLOAD_SERVICE::DOWNLOAD_FLASH_ERASE_FAILURE()")
    
        # enter bootloader:
        reset.do()   
        Report.print(ReportLevel.VERBOSE,"Waiting for controller to recover and get an CCAN address if needed.\n")       

        request_data = str(download_type) + ", " + \
            str(major_version) + "," + \
            str(minor_version) + "," + \
            str(patch_version) + "," + \
            str(size)  + "," + \
            str(crc32) + "," + \
            str(controller_crc) + "," + \
            str(modification_date) + \
            ',"' + self._filename + '",' +\
            str(self._lock_flag)
        
        ## start of dwonload:             
        self._connector.send_event("DOWNLOAD_SERVICE::DOWNLOAD_REQUEST("+ request_data + ")")
        # wait for answer:
        try:
            timeout = 1
            answer_event,index = self._connector.wait_for_event_list(timeout,bootloader_answers)
        except CCAN_Error:
            # 2nd attempt:
            self._connector.send_event("DOWNLOAD_SERVICE::DOWNLOAD_REQUEST("+ request_data + ")")
            try:
                answer_event,index = self._connector.wait_for_event_list(timeout,bootloader_answers)
            except:
                raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Download request ignored.")                                   
        

        if index == 1:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Download request rejected.")          
        if index == 2:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"File " + self._filename + " is too big for this embedded controller.")
        if index == 3:
            file_type = "Firmware" if download_type == 0 else "Configuration"
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,file_type  + " file " + self._filename + " is not suitable. Controller CRC signature in this file has not been accepted by the controller.")
        if index == 4:           
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Configuration file " + self._filename + " is not suitable. Configuration is newer than the version the firmware can suppport.") 
        if index == 5: 
            file_type = "Firmware" if download_type == 0 else "Configuration"
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,file_type  + " file " + self._filename + " is not suitable. It is newer than the version the bootloader can suppport.")
    

        chunk_size = answer_event.get_parameter_values()[0]
        already_up_to_date= answer_event.get_parameter_values()[1]

        if already_up_to_date == True and self._enforce_flag == False:
             raise CCAN_Error(CCAN_ErrorCode.TARGET_UP_TO_DATE)          

        if already_up_to_date == True and self._enforce_flag == True:
            # resend request:
            self._connector.send_event("DOWNLOAD_SERVICE::DOWNLOAD_REQUEST("+ request_data + ")")
          
        Report.print(ReportLevel.VERBOSE,"Waiting for controller to finalize erasing FLASH memory .. stay tuned!\n")

        try:
             answer_event,index  = self._connector.wait_for_event_list(8,[ready_to_rumble_event, flash_erase_failure_event ])
        except CCAN_Error as ex:
            raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)     

        if index == 1:
            raise CCAN_Error(CCAN_ErrorCode.FLASH_ERASE_FAILURE)

        # counterpart ready for download          
        number_of_chunks = math.ceil(size / chunk_size)            
        Report.print(ReportLevel.VERBOSE,"File size       : " + str(size) + " Bytes\n")
        Report.print(ReportLevel.VERBOSE,"Chunk size      : " + str(chunk_size) + " Bytes\n")
        Report.print(ReportLevel.VERBOSE,"Number of chunks: " + str(number_of_chunks)+"\n")
                            
        # number of transferred chunks before a time estimation for a download is done.
        MIN_CHUNK_COUNT_FOR_TIME_ESTIMATION = 10
    
        MEASUREMENT_OFFSET = 2
        chunk_count = 1

        while chunk_count <= number_of_chunks:

            k = chunk_count-1

            if chunk_count == MEASUREMENT_OFFSET:
                transmission_start = time.time() # skip first chunk for time measurement

            if download_type == "FIRMWARE":
                r0 = k*chunk_size + dl.minaddr()
                r1 = r0 + chunk_size-1
                if r1 > dl.maxaddr():
                    r1 = dl.maxaddr()
                data =   dl.tobinarray(start=r0, end = r1)
            else:
                r0 = k*chunk_size
                r1 = r0 + chunk_size
                if r1 > size:
                    r1 = size
                data = dl[r0:r1]
                                
            updated_event = download_event.replace_simple_parameter(list(data))

            try:
                (retries,received_chunk_count) = self.__send_chunk(timeout,updated_event,chunk_count,ack_events)                    
            except KeyboardInterrupt:
                Report.print(ReportLevel.WARN,"\nDownload has been interrupted. Check and make a new attempt..\n")                       
                # fatal..
                quit()
            except TimeoutError:                   
                raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"\nTarget did not acknowledge chunk " + str(chunk_count) +". Connection timed out.")
            if retries > 0:                 
                    Report.print(ReportLevel.DEBUG,"Transmitting chunk " +str(chunk_count)  + " with " + str(retries) + " retries.\n" )                 

            # this sleep determines the stability of the download, as the embedded system may need additional time to get ready for the next transmission
            # time.sleep(embedded_recovery_time)
            
            # time measurement:
            if chunk_count >=  MIN_CHUNK_COUNT_FOR_TIME_ESTIMATION:
                time_elapsed = time.time() - transmission_start
                average_transmission_time = time_elapsed/(chunk_count-MEASUREMENT_OFFSET)
                remaining_time = average_transmission_time*(number_of_chunks - chunk_count)
                time_information = "Remaining time: " + str(TimeDelta(remaining_time)).ljust(12)    + "    Elapsed time: " + str(TimeDelta(time_elapsed))
            else:
                time_information =""

            if chunk_count != received_chunk_count:
                Report.print(ReportLevel.DEBUG,"Missed ACK for chunk " + str(chunk_count) + "/ proceeding with chunk " + str(received_chunk_count)+"\n")
                chunk_count = received_chunk_count
                continue
            else:                  
                Report.print(ReportLevel.VERBOSE,"Transmitting chunk " +str(chunk_count).ljust(12) + time_information, my_rewind_flag = True)

            chunk_count = chunk_count + 1   
        

        self._connector.send_event("DOWNLOAD_SERVICE::DOWNLOAD_END()")  
        not_used_event, index = self._connector.wait_for_event_list(timeout,["DOWNLOAD_SERVICE::DOWNLOAD_END_ACK()", "DOWNLOAD_SERVICE::FILE_INVALID()"]) 
        if index == 0:
            Report.print(ReportLevel.VERBOSE,"\nDownload successfully completed.\n")                      
            return True
        else:
            Report.print(ReportLevel.VERBOSE,"\nDetected CRC checksum error in downloaded file. Download has been marked as invalid.\n")
        return False
  

    def __send_chunk(self,my_timeout, my_chunk, my_chunk_count, my_ack_events):
        max_retries = 5
        retries = max_retries
        while retries > 0:
            self._connector.send_event(my_chunk)  
            
            (received_event,index) = self._connector.wait_for_resolved_event_list(my_timeout,my_ack_events)        
            received_chunk_count = received_event.get_parameters().get_values()[0]        
            if index == 0:
                return (max_retries -retries, received_chunk_count)               
            else:   
                # NACK received, check whether an ACK was lost by checking the chunk count            
                received_chunk_count = received_event.get_parameters().get_values()[0]   
                if received_chunk_count == my_chunk_count +1:
                    # chunk count differs: ACK went lost, but current chunk was received, proceed with the next chunk!!
                    return (0,received_chunk_count)
                else:
                    retries = retries- 1    
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Chunk not successfully delivered")
    

    def on_interrupt(self,my_signal, frame):
        Report.print(ReportLevel.WARN,"\nDownload has been interrupted. Check and make a new attempt..\n")       
        quit()