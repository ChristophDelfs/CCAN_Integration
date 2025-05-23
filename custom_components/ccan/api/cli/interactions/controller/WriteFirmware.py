from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.cli.interactions.controller.BoardInfo import BoardInfo
from api.cli.interactions.controller.Update import Update
import os

class WriteFirmware(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
        self._connector = my_connector
        self._retries = my_retries     

    def do(self):
        file_path = self.get_filename()
        full_file_path = os.path.join(os.getenv("CCAN"), file_path)
        Report.print(ReportLevel.VERBOSE,"Used file: " + full_file_path +"\n")
        Update(self._connector, self._retries, full_file_path, my_enforce_flag= True).do()        



    def get_filename(self):
        # get controller type:
        Report.push_level(ReportLevel.WARN)
        dummy, controller_type = BoardInfo(self._connector, self._retries).do()
        Report.pop_level()
        try:
            list_of_controllers = self._platform_configuration["FIRMWARE"]
        except KeyError:
            raise CCAN_Error(CCAN_ErrorCode.CONFIGURATION_NOT_AVAILABLE,"Platform configuration has no definitions for firmware\n")
        
        for element in list_of_controllers:
           if element["controller"] == controller_type:
              return element["filename"]
        raise CCAN_Error(CCAN_ErrorCode.FILE_NOT_FOUND,"Platform configuration incomplete: no definition found for controller " + controller_type + "!\n")
        
    def on_interrupt(self,my_signal, frame):
        Report.print(ReportLevel.WARN,"\nDownload has been interrupted. Check and make a new attempt..\n")       
        quit()
