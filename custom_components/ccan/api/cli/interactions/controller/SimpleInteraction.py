from api.cli.interactions.Interaction import Interaction
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.base.Report import Report, ReportLevel

class SimpleInteraction(Interaction): 
    def __init__(self, my_connector, my_retries, request, answer, success_message):    
        super().__init__(my_connector, my_retries)    
        self._request = request
        self._answer = answer     
        self._success_message = success_message

    def do(self):        
        self.set_request(self._request)
        self.set_expected_answers([self._answer])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):         
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):          
        Report.print(ReportLevel.VERBOSE,self._success_message)
        return True
  