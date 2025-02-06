from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode


class GetEngineThreadFailures(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)      
   
    def do(self):        
        self.set_request("ENGINE_SERVICE::ENGINE_THREAD_FAILURES_REQUEST()")
        self.set_expected_answers(["ENGINE_SERVICE::ENGINE_THREAD_FAILURES_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
        self._slow_failures,self._fast_failures = my_received_event.get_parameters().get_values()
    
    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):    
        Report.print(ReportLevel.VERBOSE,"Controller had " +str(self._slow_failures) + " failures of the slow thread and " +str(self._fast_failures) + " failures of the fast thread and \n")
        return self._slow_failures, self._fast_failures
  
