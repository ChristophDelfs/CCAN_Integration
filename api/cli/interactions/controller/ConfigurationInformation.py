from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.PlatformDefaults import PlatformDefaults
from src.base.Report import Report, ReportLevel
import time


class ConfigurationInformation: 
    def __init__(self, my_connector, my_retries):          
        self._connector = my_connector
        self._retries = my_retries

    def do(self):
        results = {}
        results[PlatformDefaults.UPDATE_SECTION_CONFIGURATION] =  ConfigurationInformationGetter(self._connector, self._retries,PlatformDefaults.UPDATE_SECTION_CONFIGURATION).do()
        results[PlatformDefaults.UPDATE_SECTION_BOOTLOADER]    = ConfigurationInformationGetter(self._connector, self._retries,PlatformDefaults.UPDATE_SECTION_BOOTLOADER).do()
        results[PlatformDefaults.UPDATE_SECTION_FIRMWARE]      = ConfigurationInformationGetter(self._connector, self._retries,PlatformDefaults.UPDATE_SECTION_FIRMWARE).do()

        result_type_string = ["Bootloader","Firmware","Configuration"]

        Report.print(ReportLevel.VERBOSE, f"{'Topic:':<20}" + f"{'Date':20}" + f"{'Version':20}" +  f"{'File:':40}" +" \n")         
        for result_type in results:            
            Report.print(ReportLevel.VERBOSE,f"{result_type_string[result_type]:<20}")
            result = results[result_type]
            
            version = result[0]
            version_info = str(version[0]) + "." + str(version[1]) + "." + str(version[2])

            date = time.localtime(result[1])
            date_string = str(date.tm_mday) + "." + str(date.tm_mon) + "." + str(date.tm_year)            
            
            filename = result[2]
            if len(filename) == 0 and result_type == PlatformDefaults.UPDATE_SECTION_CONFIGURATION:
                Report.print(ReportLevel.VERBOSE,f"{'':20}" + f"{version_info:20}" +"Default configuration\n")       
            elif len(filename) == 0 and result_type == PlatformDefaults.UPDATE_SECTION_FIRMWARE:
                Report.print(ReportLevel.VERBOSE,f"{'':20}" + f"{'':20}" + "Unavailable\n") 
            elif len(filename) == 0:
                Report.print(ReportLevel.VERBOSE,f"{'':20}" + f"{'':20}" + "Bootloader (flashed)\n") 
            else:                                                         
                Report.print(ReportLevel.VERBOSE, f"{date_string:20}" + f"{version_info:20}" +  f"{filename:40}" +" \n")     



    


      
class ConfigurationInformationGetter(Interaction):
    def __init__(self, my_connector, my_retries, my_section):    
        super().__init__(my_connector, my_retries)
        self._version = []
        self._date = None
        self._filename = None
        self._connector = my_connector
        self._section = my_section

    def do(self):        
        self.set_request("CONFIG_SERVICE::INFO_REQUEST(" + str(self._section) + ")")
        
        # set all, the right one will come..
        answers = ["CONFIG_SERVICE::CONFIGURATION_INFO()","CONFIG_SERVICE::BOOTLOADER_INFO()","CONFIG_SERVICE::FIRMWARE_INFO()"]
        self.set_expected_answers(answers)
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        (version_major, version_minor, version_patch, date, filename) = my_received_event.get_parameters().get_values()
        self._version = [ version_major, version_minor, version_patch]
        self._date = date
        self._filename = filename
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)

    def on_iteration_end(self):
        return

    def on_loop_end(self):     
        return self._version, self._date, self._filename

