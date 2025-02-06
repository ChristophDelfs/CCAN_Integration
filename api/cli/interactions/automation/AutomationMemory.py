from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationMemory(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file):         
        super().__init__( my_connector, my_waiting_time, my_retries, my_automation_file)       
        self._free_ram = {}
        self._used_ram = {}
        self._total_ram = {}
    
    def do(self):   
        self.set_request("MEMORY_SERVICE::MEMORY_USAGE_REQUEST()")
        self.set_expected_answers(["MEMORY_SERVICE::MEMORY_USAGE_RESULT()"])
        return super().do()

    def on_iteration_end(self):
        return
  
    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):    
        receiver = my_received_event.get_sender_address()     
        free_ram, used_ram = my_received_event.get_parameters().get_values()
        
        self._free_ram[receiver]  = free_ram
        self._used_ram[receiver]  = used_ram
        self._total_ram[receiver] = free_ram + used_ram
        return False      

    def on_loop_end(self):
        if len(self._free_ram) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

    
        Report.print(ReportLevel.VERBOSE, f"{'Controller name':20}" + f"{'Address:':10}" +f"{'Total RAM [Bytes]':20}" + f"{'Free RAM [Bytes]:':20}" +  f"{'Used RAM [Bytes]:':20}" "\n")         
        for address in self._free_ram:  
            controller_name = self._base.get_controller_name(address)              
            Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:20}" +'{:<10}'.format(address) + f"{self._total_ram[address]:<20}" +  f"{self._free_ram[address]:<20}" +  f"{self._used_ram[address]:<20}" "\n")                                    

        return [self._free_ram, self._used_ram, self._total_ram]    




       

