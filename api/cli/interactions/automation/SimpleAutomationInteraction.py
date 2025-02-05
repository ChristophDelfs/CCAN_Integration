from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class SimpleAutomationInteraction(AutomationInteraction): 
    def __init__(self, my_cli, my_waiting_time, my_retries, my_automation_file, my_request, my_answer, my_success_message, my_method= None): 
        
        super().__init__(my_cli, my_waiting_time, my_retries, my_automation_file)            
        self.__cli = my_cli
        self._request = my_request
        self._expected_answers = [my_answer]
        self._success_message = my_success_message
        self._result = {}
        self._answer_value_evaluation_method = my_method


        
    def do(self):     
        return super().do()

    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):

        if self._answer_value_evaluation_method is not None:
            result =  self._answer_value_evaluation_method(my_received_event.get_parameters().get_values())
        else:
            result = True

        self._result[my_received_event.get_sender_address()] = result
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):     
        if len(self._result) == 0:
            raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)

        Report.print(ReportLevel.VERBOSE,str(len(self._result)) + " controllers have responded:\n")
                    

        if self._answer_value_evaluation_method == None:
            for address in self._result:
                Report.print(ReportLevel.VERBOSE,str(address) + "\n")
            Report.print(ReportLevel.VERBOSE, self._success_message)
                                        
        return [self._result]