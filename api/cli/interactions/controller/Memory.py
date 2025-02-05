from src.cli.interactions.Interaction import Interaction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class Memory(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
        self._free_ram = 0
        self._used_ram = 0        
  
    def do(self):
        
        self.set_request("MEMORY_SERVICE::MEMORY_USAGE_REQUEST()")
        self.set_expected_answers(["MEMORY_SERVICE::MEMORY_USAGE_RESULT()"])

        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self._free_ram, self._used_ram = my_received_event.get_parameters().get_values()
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Controller may not support this function or controller may not run firmware.")       

    def on_iteration_end(self):
        return

    def on_loop_end(self):     
        Report.print(ReportLevel.VERBOSE, "Total RAM: " + str(self._free_ram + self._used_ram)  + " Bytes         Free RAM: " + str(self._free_ram) + " Bytes       Used RAM: " + str(self._used_ram)+ " Bytes\n")
        return self._free_ram, self._used_ram

