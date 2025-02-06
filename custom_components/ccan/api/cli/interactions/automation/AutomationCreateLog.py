from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction
from api.base.Report import Report, ReportLevel
import signal
import os

class AutomationCreateLog(AutomationInteraction): 
    def __init__(self,  my_connector, my_waiting_time, my_retries, my_file, my_automation_file):                       
        self._connector = my_connector       
        self._file = my_file

        super().__init__(my_connector,  my_waiting_time, my_retries, my_automation_file)      
        signal.signal(signal.SIGINT, self.on_interrupt)
        
    def do(self):
        self.set_request(None)
        self.set_expected_answers(None)
        self._logged_events = 0

        # open log file:
        if self._file == False:
            log_filename = os.path.basename(self._connector.get_automation_filename())
        else:
            log_filename = self._file

        log_path = self._platform_configuration["LOG_FILES"]["PATH"]
        full_path = os.sep.join([os.environ["CCAN"],log_path, log_filename+".log"]) 

        self._log_file = open(full_path, 'wb')
        self._connector._write(self._log_file)
        Report.print(ReportLevel.VERBOSE,"Logging started into "+  full_path + "\n")

        super().do(collect_answers= False)

    def before_send(self):
        pass

    def on_receive(self,my_received_event, my_index):        
        if my_received_event is not None and my_received_event.is_complete() == True:
            my_received_event.add_binary_state_to_file(self._log_file)
            self._log_file.flush() # update immediately!
            self._logged_events += 1
        return False  

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):      
        self._log_file.close()   
        Report.print(ReportLevel.VERBOSE,'{:>4}'.format(self._logged_events) + " events logged. Logging ended.\n")
        return self._logged_events      

    def on_interrupt(self,my_signal, frame):
        self.terminate_loop()            
        Report.print(ReportLevel.VERBOSE,"\r")   

