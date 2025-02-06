from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationSwID(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file):         
        super().__init__( my_connector, my_waiting_time, my_retries, my_automation_file)       
        self._sw_id = {}
    
    def do(self):   
        self.set_request("CONFIG_SERVICE::GET_SW_ID()")
        self.set_expected_answers(["CONFIG_SERVICE::SW_ID()"])
        return super().do()

    def on_iteration_end(self):
        return
  
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
        
        self._sw_id[my_received_event.get_sender_address()] = id_str

        return False       

    def on_loop_end(self):
        if len(self._sw_id) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

        controller_name_length = self._base.get_controller_name_max_length()

        Report.print(ReportLevel.VERBOSE, f"{'Controller name':{controller_name_length}}"  + f"{'Address:':10}" + f"{'SW ID:':10}"  +"\n")         
        for receiver in self._sw_id:                
            controller_name = self._base.get_controller_name(receiver)           
            Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:{controller_name_length}}"  + '{:<10}'.format(receiver) +  f"{self._sw_id[receiver]:20}" + "\n")                 
     
        return [self._sw_id]

       

