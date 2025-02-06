from api.cli.interactions.Interaction import Interaction
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from api.base.Report import Report, ReportLevel

class ProcessorLoad(Interaction): 
    def __init__(self, my_connector, my_waiting_time):    
        super().__init__(my_connector, my_waiting_time)
        self.__average_load_during_list_minute = 0
        self.__maximum_load_during_last_minute = 0
  
    def do(self):
        
        self.set_request("LIFE_SERVICE::PROCESSOR_LOAD_REQUEST()")
        self.set_expected_answers(["LIFE_SERVICE::PROCESSOR_LOAD_REPLY()"])

        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self.__average_load_during_list_minute, self.__maximum_load_during_last_minute = my_received_event.get_parameters().get_values()
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT,"Controller may not support this function or controller may not run firmware.")       

    def on_iteration_end(self):
        return

    def on_loop_end(self):     
        Report.print(ReportLevel.VERBOSE,"Average processor load in last 60s period : "  + '{:2g}'.format(self.__average_load_during_list_minute) + "%\n")
        Report.print(ReportLevel.VERBOSE,"Maximum processor load in last 60s period : "  + '{:2g}'.format(self.__maximum_load_during_last_minute) + "%\n")       
        return self.__average_load_during_list_minute, self.__maximum_load_during_last_minute

    def on_interrupt(self,my_signal, frame):    
        return

