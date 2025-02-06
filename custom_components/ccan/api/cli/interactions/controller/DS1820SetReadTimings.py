from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DS1820SetReadTimings(Interaction): 
    def __init__(self, my_connector, my_retries, my_pulldown_period, my_floating_period_before_sampling, my_floating_period_after_sampling, my_recovery_period):    
        super().__init__(my_connector, my_retries)
      
        self._pulldown_period = my_pulldown_period
        self._floating_period_before_sampling = my_floating_period_before_sampling
        self._floating_period_after_sampling = my_floating_period_after_sampling
        self._recovery_period = my_recovery_period

    def do(self):        
        # defaults:
        self.set_request(f"DS1820_SERVICE::DS1820_SERVICE_SET_READ_TIMINGS({self._pulldown_period}, {self._floating_period_before_sampling}, {self._floating_period_after_sampling}, {self._recovery_period})")
        self.set_expected_answers( ["DS1820_SERVICE::DS1820_SERVICE_RESULT_CODE()"])          
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
         self._result = my_received_event.get_parameter_values()[0]

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):    
        if self._result == 0:
            Report.print(ReportLevel.VERBOSE,"Read timings changed.\n")          
        return True
