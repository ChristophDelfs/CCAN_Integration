from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class DebugEventTest(Interaction): 
    def __init__(self, my_connector, my_retries,my_repetitions):    
        super().__init__(my_connector, my_retries)         
        self._repetitions = my_repetitions   
        if my_repetitions < 1  or my_repetitions > 255:         
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT,"Only 1..255 repetitions are allowed (your value: " + str(my_repetitions) +").")
  
    def do(self):        
        self.set_request("DEBUG_SERVICE::FLOOD_WITH_EVENTS("+str(self._repetitions)+")")
        self.set_expected_answers(None)
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):                
        return True

    def on_receive_failure(self, my_exception):
        return

    def on_iteration_end(self):
        return

    def on_loop_end(self):                                 
        Report.print(ReportLevel.VERBOSE,"EventTest has been started.\n")
        return True


  
