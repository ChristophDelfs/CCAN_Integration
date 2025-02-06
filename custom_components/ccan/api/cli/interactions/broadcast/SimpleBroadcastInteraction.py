from api.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class SimpleBroadcastInteraction(BroadcastInteraction): 
    def __init__(self, my_cli, my_waiting_time, my_retries, my_request, my_answer, my_success_message, my_method= None): 
        
        super().__init__(my_cli, my_waiting_time, my_retries)            
        self.__cli = my_cli
        self._request = my_request
        self._answer = my_answer
        self._success_message = my_success_message
        self._result = {}
        self._answer_value_evaluation_method = my_method


        
    def do(self):     
        self.set_request(self._request)
        self.set_expected_answers([self._answer])
        return super().do()

    def before_send(self):
        pass
       
    def get_result(self):
        return self._result

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
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

        Report.print(ReportLevel.VERBOSE,str(len(self._result)) + " controllers have responded:\n")
                    

        if self._answer_value_evaluation_method == None:
            for address in sorted(list(self._result)):
                Report.print(ReportLevel.VERBOSE,str(address) + "\n")
            Report.print(ReportLevel.VERBOSE, self._success_message)
          
        return self._result