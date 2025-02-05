from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.PlatformServices import PlatformServices
import time
from src.cli.AutomationDegradationTOC import AutomationDegradationTOC

class AutomationDegradationStatus(AutomationInteraction): 
    def __init__(self,  my_connector, my_waiting_time, my_retries, my_automation_file):                 
        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)
        self._connector = my_connector  
        self._degraded_elements = {}     

        self._toc = AutomationDegradationTOC(my_connector.get_description_dictionary(), my_connector. get_instance_dictionary())

        
    def do(self):     
        self.set_request("LIFE_SERVICE::DEGRADATION_STATUS_REQUEST()")
        self.set_expected_answers( ["LIFE_SERVICE::DEGRADATION_STATUS_REPLY_ITEM()","LIFE_SERVICE::DEGRADATION_STATUS_REPLY_COMPLETED()"])
        return super().do(collect_answers= False, wait_for_expected_answers= False)
      
    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):       
        if my_index == 1:
            self._degraded_elements[my_received_event.get_sender_address()] = True          
        else:           
            self._toc.insert(my_received_event.get_sender_address(),my_received_event.get_parameter_values())        
        if len(self._degraded_elements) == self._base.get_number_of_controllers_in_network():        
            return True           
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self): 
           
        if self._toc.get_size() > 0:
            Report.print(ReportLevel.VERBOSE,"\nThe following elements are degraded:\n")
            Report.print(ReportLevel.VERBOSE, f"{'Typ':20}" + f"{'Name:':60}" +f"{'connected to':25}" +  f"{'Description:':60}"  + f"{'Status:':20}" "\n")         
            for degraded_element in self._toc:
                Report.print(ReportLevel.VERBOSE.VERBOSE, f"{degraded_element.type:20}" + f'{degraded_element.name:60}' + f"{degraded_element.connection:25}" + f"{degraded_element.code_explanation:60}" + f"{degraded_element.status_explanation:20}" "\n")                                    
        else:
              Report.print(ReportLevel.VERBOSE.VERBOSE,"No degradation detected.\n")
        return [self._degraded_elements]

