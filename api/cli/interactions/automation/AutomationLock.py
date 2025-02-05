from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationLock(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file):         
        super().__init__(my_connector, my_waiting_time, my_retries, my_automation_file)            
        self.__ack_received = {}

    def do(self):     
        self.set_request("LIFE_SERVICE::LOCK_BOOTLOADER()")
        self.set_expected_answers(["LIFE_SERVICE::LOCK_BOOTLOADER_ACK()"])
        return super().do()
      
    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):            
        ccan_address = my_received_event.get_sender_address()     
        self.__ack_received[ccan_address] = True
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self): 
        if len(self.__ack_received) == 0:
            raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Feature is only available if controller runs in bootloader mode.")    
    
        Report.print(ReportLevel.VERBOSE,"Bootloader lock acknowledged by " + str(len(self.__ack_received)) + " controllers:\n")
        for ccan_address in self.__ack_received:
             Report.print(ReportLevel.VERBOSE,"Controller with address " + str(ccan_address) +"\n")
        Report.print(ReportLevel.VERBOSE,"Responding controllers are locked in bootloder mode. You need to issue a reset to unlock the controllers.\n")     
        return [self.__ack_received]
