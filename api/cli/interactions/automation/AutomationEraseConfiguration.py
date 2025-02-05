from src.cli.interactions.automation.SimpleAutomationInteraction import SimpleAutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class AutomationEraseConfiguration(SimpleAutomationInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries, my_automation_file):                           
        super().__init__(my_connector, my_waiting_time, my_retries, my_automation_file, request="CONFIG_SERVICE::ERASE_CONFIG()",
                                                   answer= "CONFIG_SERVICE::ERASE_CONFIG_ACK()",
                                                   success_message="Configuration has been erased. Default configuration is active now." )  
   

    def do(self):        
       return super().do()