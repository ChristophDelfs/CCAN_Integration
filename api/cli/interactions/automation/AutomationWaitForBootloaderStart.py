from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationWaitForBootloaderStart(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, bootloader_expected): 
        
        super().__init__(my_connector, my_waiting_time, my_retries)              
        self.__ack_received = []
        self._bootloader_expected = bootloader_expected

    def do(self):     
        self.set_request(None)
        parameter = str("1")
        if self._bootloader_expected == False:
            parameter = str("2")
     
        self.set_expected_answers(["LIFE_SERVICE::CONTROLLER_RESET()"])
        return super().do()
      
    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):            
        ccan_address = my_received_event.get_sender_address()       
        my_received_event.print_with_colors(True)         
        self.__ack_received.append(ccan_address)                  
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self): 
        if len(self.__ack_received) == 0:
            raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"NO responses received.")    
    
        Report.print(ReportLevel.VERBOSE,"Bootloader start confirmed by " + str(len(self.__ack_received)) + " controllers:\n")
        for ccan_address in sorted(list(self.__ack_received)):
             Report.print(ReportLevel.VERBOSE,"Controller with address " + str(ccan_address) +"\n")       
        return self.__ack_received

