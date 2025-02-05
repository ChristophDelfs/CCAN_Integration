from src.cli.interactions.automation.SimpleAutomationInteraction import SimpleAutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

"""
        Function ships an event to the connected target.
        The event is described as symbolic expression or a resolved event and supports device, application and protocol events:
        For device events all addressing types are supported. The addressing mode needs to be supplied.
        Examples:
        
        DeviceEventAddressing:    "DEA my_state_machine::INPUT_TRANSITION(current_state = 2, new_state =4)"
        DirectEventAddressing:    "DIR my_counter::RESTART()"
        OutboundEventAdressing:   "OUT my_counter::RESTART()" 
        IndirectEventAddressing:  "IND my_state_machine::INPUT_TRANSITION(current_state = 2, new_state =4)"
        
        Application Events:       "LIFE_SERVICE::PING()"
        
        Protocol Events:
        HCAN-Event                "HCAN(path = "SFP/HES")::POWER_GROUP_ON(gruppe= 7)"
        
        Remarks:
        Parameter arguments can be provided with or with no argument names. If argument names are given, the order of the arguments is corrected if necessary.
        """                     
class AutomationSendEvent(SimpleAutomationInteraction):
    def __init__(self, my_connector, my_waiting_time, my_retries, my_event, my_automation_file): 
    
      
        super().__init__(my_connector, my_waiting_time, my_retries, my_automation_file, None,None,"")
    
        try:
            self.set_request(my_event)            
        except Exception as e:          
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_EVENT,f"Failing event: '{my_event}'.")
        self.set_expected_answers(None)
        self.enforce_no_wait_for_reply()
        self.enforce_no_automation_check()
    
      
    def do(self):    
        # suppress output 
        #Report.push_level(ReportLevel.WARN)
        super().do()
        #Report.pop_level()
        Report.print(ReportLevel.VERBOSE, "Done\n")
        return True

   
             
   