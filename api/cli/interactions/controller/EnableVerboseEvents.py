from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class EnableVerboseEvents(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)         
  
    def do(self):        
        self.set_request("ENGINE_SERVICE::ENABLE_VERBOSE_EVENTS()")
        self.set_expected_answers(["ENGINE_SERVICE::ENABLE_VERBOSE_EVENTS_ACK()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):         
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):          
        Report.print(ReportLevel.VERBOSE,"Verbose events have been enabled.\n")
        return True
  
