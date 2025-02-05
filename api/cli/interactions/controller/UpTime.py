from src.cli.interactions.Interaction import Interaction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
import math

class UpTime(Interaction): 
    def __init__(self, my_connector, my_retries):    
        super().__init__(my_connector, my_retries)
        self._average_load_during_list_minute = 0
        self._maximum_load_during_last_minute = 0
        self._connector = my_connector
  
    def do(self):
        
        self.set_request("LIFE_SERVICE::UPTIME_REQUEST()")
        self.set_expected_answers(["LIFE_SERVICE::UPTIME_REPLY()"])
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):
        self._uptime = my_received_event.get_parameters().get_values()[0]
        return True

    def on_receive_failure(self, my_exception):
        raise CCAN_Error(CCAN_ErrorCode.TIME_OUT)    

    def on_iteration_end(self):
        return

    def on_loop_end(self):        
        days = math.floor((self._uptime / (60*60*24)))
        hours = math.floor((self._uptime - days*60*60*24)/(60*60))
        minutes = math.floor((self._uptime - days*60*60*24 - hours*60*60)/60)
        seconds = self._uptime % 60

        Report.print(ReportLevel.VERBOSE,"Controller is up for " + str(days) + " days, " + str(hours) + " hours, " + str(minutes) + " minutes and " + str(seconds) + " seconds\n" )

        return self._uptime
   