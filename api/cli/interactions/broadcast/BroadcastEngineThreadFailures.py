from src.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastEngineThreadFailures(BroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_waiting_time, my_retries)              
        self._slow_failures = {}       
        self._fast_failures = {}

    def do(self):     
        self.set_request("ENGINE_SERVICE::ENGINE_THREAD_FAILURES_REQUEST()")
        self.set_expected_answers(["ENGINE_SERVICE::ENGINE_THREAD_FAILURES_REPLY()"])
        return super().do()
      
    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):            
        slow_failures,fast_failures = my_received_event.get_parameters().get_values()  
        self._slow_failures[my_received_event.get_sender_address()] = slow_failures
        self._fast_failures[my_received_event.get_sender_address()] = fast_failures              
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self): 
           
        Report.print(ReportLevel.VERBOSE,"Engine Thread Failure Information received by " + str(len(self._slow_failures)) + " controllers:\n")
        Report.print(ReportLevel.VERBOSE, f"{'Address:':<10}" + f"{'Slow Thread Failures':25}" + f"{'Fast Thread Failures:':25}\n")     
        for address in sorted(list(self._slow_failures)):           
           Report.print(ReportLevel.VERBOSE, f"{address:<10}" + f"{self._slow_failures[address]:<25}" + f"{self._fast_failures[address]:<25}\n")     
     
        return self._slow_failures, self._fast_failures

