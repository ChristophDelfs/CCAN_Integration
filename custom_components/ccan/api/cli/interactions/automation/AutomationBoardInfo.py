from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.PlatformServices import PlatformServices
import time

class AutomationBoardInfo(AutomationInteraction): 
    def __init__(self,  my_connector, my_waiting_time, my_retries, my_automation_file):                 
        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)
        self._connector = my_connector  
        
    def do(self):                 
        result = []
        controller_name_length = self._base.get_controller_name_max_length()

        Report.print(ReportLevel.VERBOSE,f"{'Typ':20}" +  f"{'Controller name':{controller_name_length}}"+ f"{'CCAN Address':15}" + f"{'UUID':40}"+   "\n")
        for address in self._base.get_ccan_addresses_from_automation():  
            uuid = self._base.get_uuid(address)
            current_address = self._base. get_current_address_via_uuid(uuid)             
            controller_name =  self._base.get_controller_name(address)
            controller_type = self._base.get_controller_type(address)
            Report.print(ReportLevel.VERBOSE,  f"{controller_type:<20}" + f"{controller_name:{controller_name_length}}"+  f"{str(address):15}" + f"{uuid:40}" + "\n")

            result.append((controller_type, controller_name, current_address, uuid))
                      
        return result

