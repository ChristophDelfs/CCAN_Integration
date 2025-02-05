from src.cli.interactions.automation.SimpleAutomationInteraction import SimpleAutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationSetVariable(SimpleAutomationInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries, my_variable_name,my_value, my_automation_file): 
        super().__init__(my_connector, my_waiting_time, my_retries, my_automation_file,None,None,"Ok")
    
        (destination_address,variable_id) = my_connector.identify_variable(my_variable_name)   
        self.set_request("VARIABLE_SERVICE::SET(" + str(variable_id) +","  + str(my_value) +")")
        self.set_expected_answers(None)
        self.enforce_no_automation_check()
        self.enforce_no_wait_for_reply()      
        
    def do(self):    
        # suppress output 
        Report.push_level(ReportLevel.WARN)
        super().do()
        Report.pop_level()
        Report.print(ReportLevel.VERBOSE,"Done\n")
        return None
    

