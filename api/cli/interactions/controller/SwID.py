from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.Report import Report, ReportLevel

class SwID(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)         
  
    def do(self):        
        self.set_request("CONFIG_SERVICE::GET_SW_ID()")
        self.set_expected_answers(["CONFIG_SERVICE::SW_ID()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
        id_value = my_received_event.get_parameters().get_values()[0]

        if id_value == 0:
            id_str = "BOOTLOADER (LOCKED)"       
        elif id_value == 1:
            id_str = "BOOTLOADER"             
        elif  id_value == 2:
            id_str = "FIRMWARE"
        else:
            id_str ="UNKNOWN SW"
        
        self.__id_str = id_str

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):    
        Report.print(ReportLevel.VERBOSE,"Controller runs " + self.__id_str + ".\n")
        return self.__id_str
  
