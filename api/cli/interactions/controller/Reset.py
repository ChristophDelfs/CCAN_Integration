from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class Reset(Interaction): 
    def __init__(self, my_connector, my_retries, my_wait_for_startup = False):    
        super().__init__(my_connector, my_retries, my_waiting_time= 10)       
        self._wait_for_startup = my_wait_for_startup  
  
    def do(self):        
        self.set_request("LIFE_SERVICE::RESET_REQUEST()")
        if self._wait_for_startup == True:
             self.set_expected_answers(["LIFE_SERVICE::CONTROLLER_RESET()"])           
        else:
            self.set_expected_answers(["LIFE_SERVICE::RESET_ACK()"])

        return super().do()

    def before_send(self):
        return

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):      
        if self._wait_for_startup == False: 
            Report.print(ReportLevel.VERBOSE,"Reset has been acknowledged by controller.\n")
        else:
            Report.print(ReportLevel.VERBOSE,"Controller has started bootloader.\n")

        if my_index == 0 and self._wait_for_startup == True:
            return False
        else:
            return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Reset has not been acknowledged.")    

    def on_iteration_end(self):
        return

    def on_loop_end(self):                                 
        return True
