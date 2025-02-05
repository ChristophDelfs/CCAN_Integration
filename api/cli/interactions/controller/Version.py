from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class Version(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)         
  
    def do(self):        
        self.set_request("CONFIG_SERVICE::GET_VERSION()")
        self.set_expected_answers(["CONFIG_SERVICE::GET_VERSION_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):         
       version_data = my_received_event.get_parameters().get_values()
       self._sw_version = version_data[0:3]
       self._sw_version_string = str(version_data[0]) +"." + str(version_data[1]) + "." + str(version_data[2])
       self._configuration_version = version_data[3:6]
       self._configuration_version_string = str(version_data[3]) +"." + str(version_data[4]) + "." + str(version_data[5])

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):          
        Report.print(ReportLevel.VERBOSE,"Controller runs SW version " + self._sw_version_string + " and configuration with version " + self._configuration_version_string + ".\n")
        return self._sw_version, self._configuration_version
  
