from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class Lock(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)         
  
    def do(self):        
        self.set_request("LIFE_SERVICE::LOCK_BOOTLOADER()")
        self.set_expected_answers(["LIFE_SERVICE::LOCK_BOOTLOADER_ACK()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
        Report.print(ReportLevel.VERBOSE,"Lock has been acknowledged by controller. Controller will not leave bootloader mode. You need to reset the controller to remove lock.\n")
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Feature is only available if controller runs in bootloader mode.")    

    def on_iteration_end(self):
        return

    def on_loop_end(self):                                 
        return True


  
