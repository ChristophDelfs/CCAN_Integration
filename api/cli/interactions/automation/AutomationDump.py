from src.cli.interactions.automation.AutomationInteraction import AutomationInteraction
import signal
from src.base.Report import Report, ReportLevel
from src.events.HCAN_Event import HCAN_Event

class AutomationDump(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries, my_filter, my_automation_file): 
        
        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)      
        self._filter = my_filter    
        signal.signal(signal.SIGINT, self.on_interrupt)
        my_connector.run_on_updated_automation(self.say_hello)

    def do(self):        
        self.set_request(None)
        self.set_expected_answers(None)

        super().do(collect_answers= False)

    def say_hello(self):
        Report.print(ReportLevel.VERBOSE,"Continuing to dump all events based on updated automation.\n")   

    def before_send(self):
        pass

    def on_receive(self,my_received_event, my_index):
        if my_received_event is not None and my_received_event.is_complete():
            my_received_event.print_with_colors(True)       
            if self._filter =="hex":
                my_received_event.set_hex_mode()
            if self._filter != "no_hcan" or not isinstance(my_received_event, HCAN_Event):
                Report.print(ReportLevel.VERBOSE,"\r"+str(my_received_event)+"\n")
        return False  

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):    
        return       

    def on_interrupt(self,my_signal, frame):
        self.terminate_loop()               
        Report.print(ReportLevel.VERBOSE,"\r")   