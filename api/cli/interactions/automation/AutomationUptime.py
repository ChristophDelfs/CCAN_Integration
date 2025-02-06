from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
import math

class AutomationtUptime(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file): 
        
        super().__init__(my_connector, my_waiting_time, my_retries, my_automation_file)                      
        self._uptime = {}       

    def do(self):     
        self.set_request("LIFE_SERVICE::UPTIME_REQUEST()")
        self.set_expected_answers(["LIFE_SERVICE::UPTIME_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self._uptime[my_received_event.get_sender_address()] = my_received_event.get_parameters().get_values()[0]
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):     
        if len(self._uptime) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

        controller_name_length = self._base.get_controller_name_max_length()


        Report.print(ReportLevel.VERBOSE,f"{'Controller name':{controller_name_length}}"+ f"{'Address:':<10}" + f"{'Days':10}" + f"{'Hours:':10}" +  f"{'Minutes:':10}" +f"{'Seconds:':10}"+ " \n")         
        for address in sorted(list(self._uptime)):

            controller_name = self._base.get_controller_name(address)     

            uptime = self._uptime[address]      

            days = math.floor((uptime / (60*60*24)))
            hours = math.floor((uptime - days*60*60*24)/(60*60))
            minutes = math.floor((uptime - days*60*60*24 - hours*60*60)/60)
            seconds = uptime % 60

            Report.print(ReportLevel.VERBOSE.VERBOSE, f"{controller_name:{controller_name_length}}"+ '{:<10}'.format(address) + f"{days:<10}" +  f"{hours:<10}" +  f"{minutes:<10}" +   f"{seconds:<10}" + "\n")                                    

        return [self._uptime]    


