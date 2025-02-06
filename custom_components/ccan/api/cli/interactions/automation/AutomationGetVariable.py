from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
import re
from api.base.PlatformDefaults import PlatformDefaults

class AutomationGetVariable(AutomationInteraction):
    OUTPUT_WIDTH = 85

    def __init__(self, my_connector, my_waiting_time, my_retries, my_variable_name,my_automation_file): 
    
        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)    
                 
        variable_names = my_connector.get_variable_names()
        matches = []
        try:
            for variable_name in variable_names:
                if  re.search(my_variable_name, variable_name, re.IGNORECASE) is not None:                
                    matches.append(variable_name)
        except:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT," argument <" + my_variable_name + "> is no valid regular expression.")  

        if len(matches) == 0:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT," argument <" + my_variable_name + "> does not fit to any variable name")


        matches.sort()
        self._matches = matches
        self.__result = []
     
    def do(self):
        Report.print(ReportLevel.VERBOSE, f"{'Variable Name':100}" + f"{'Value':30}"+ "\n")  
        for match in self._matches:
            self._current_match = match
          
            try:
                (full_name,variable_id) = self._connector.identify_variable(match)   
                self._connector.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)
                self.set_request("VARIABLE_SERVICE::GET(" + str(variable_id) +")")
                self.set_expected_answers(["VARIABLE_SERVICE::GET_RESULT()"])          
                super().do(collect_answers= False)
            except:
                pass

        Report.print(ReportLevel.VERBOSE,str(len(self.__result)) + " variables collected.\n")
        return [self._matches, self.__result]

    def before_send(self):
        pass

    def on_receive(self,my_received_event, my_index):     
        id, value =    my_received_event.get_parameters().get_values()
        Report.print(ReportLevel.VERBOSE, f"{self._current_match.ljust(100,'.'):100}" + f"{str(value):30}"+ "\n")       
        self.__result.append(value)    
        return True


    def on_iteration_end(self):
        return

    def on_loop_end(self):        
        return self.__result
            

  

   
             
   