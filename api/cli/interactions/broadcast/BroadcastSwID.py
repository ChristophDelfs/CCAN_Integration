from src.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastSwID(BroadcastInteraction): 
    def __init__(self, my_cli, my_waiting_time, my_retries): 
        
        super().__init__(my_cli, my_waiting_time, my_retries)            
        self.__cli = my_cli
        self._sw_id = {}

        
    def do(self):     
        self.set_request("CONFIG_SERVICE::GET_SW_ID()")
        self.set_expected_answers(["CONFIG_SERVICE::SW_ID()"])
        super().do()

    def before_send(self):
        pass
       
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

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):     
        if len(self._sw_id) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

        Report.print(ReportLevel.VERBOSE, f"{'Address':10}" + f"{'SW ID':20}" + " \n")         
        for address in sorted(list(self._sw_id)):  
            sw_id = self._sw_id[address]
            Report.print(ReportLevel.VERBOSE.VERBOSE,'{:<10}'.format(address) +  f"{sw_id:20}" + "\n")                                    


        return [self._sw_id]

