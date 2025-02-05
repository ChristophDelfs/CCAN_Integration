import signal
from src.base.Report import Report, ReportLevel
from src.cli.interactions.Interaction import Interaction
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from src.base.PlatformDefaults import PlatformDefaults
from src.cli.interactions.automation.AutomationBase import AutomationBase
from src.cli.interactions.Interaction import Interaction
import time
import sys

class AutomationInteraction(Interaction):
    AUTOMATION_MAX_WAITING_TIME = 2

    def __init__(self, my_connector, my_waiting_time, my_retries,my_automation_file,my_mode = "MIN"):
        super().__init__(my_connector, my_retries)

        self._connector = my_connector
        self._waiting_time = my_waiting_time
        self._end_loop = False
        self._collected_answers = []      
        self._collected_values  = {}     
        self._retries = my_retries  
        self._check_automation = True
        self._no_wait_for_reply = False
        my_connector.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)

        Report.push_level(ReportLevel.WARN)
        try: 
            self._base = AutomationBase(my_connector, my_waiting_time, my_automation_file,my_mode)      
        except CCAN_Error as ex:
             Report.pop_level()
             raise ex
        self._waiting_time = AutomationInteraction.AUTOMATION_MAX_WAITING_TIME       

        self._number_of_expected_answers = self._base.get_number_of_controllers_in_automation()

        signal.signal(signal.SIGINT, self.on_interrupt)
        Report.pop_level()
  
    def enforce_no_automation_check(self):
        self._check_automation = False

    def enforce_no_wait_for_reply(self):
        self._no_wait_for_reply = True

    def terminate_loop(self):
        self._end_loop = True

    def do(self, collect_answers = True, wait_for_expected_answers = True):

        self._end_loop = False
        retries = self._retries

        while self._end_loop == False and retries != 0:
      
            self.before_send()

            number_of_expected_answers = self._number_of_expected_answers

            # send:       
            if self._request != None:
                self._connector.send_event(self._request)
           
            if self._no_wait_for_reply == True:
                return None

            remaining_time = self._waiting_time
            start_time = time.time()
            
            while remaining_time > 0:                            
                # receive:                 
                try:
                    if isinstance(self._expected_answers,list):
                        received_event, index  = self._connector.wait_for_event_list(Interaction.timeout,self._expected_answers)
                    else:                        
                        received_event = self._connector.receive_event(Interaction.timeout)
                        index = -1
                                
                    self._end_loop = self.on_receive(received_event, index) or  self._end_loop              

                    # collect messages only, if you expect specific answers:
                    if  collect_answers == True:                      
                        self._collected_values[received_event.get_sender_address()] = received_event.get_parameters().get_values()    
                        self._collected_answers.append( (received_event, index))
                
                except CCAN_Error as ex:
                    if ex.get_code() != CCAN_ErrorCode.TIME_OUT:
                        print(ex, file=sys.stderr)
                    pass

                if self._end_loop == True:
                    break

                if isinstance(self._expected_answers,list) and wait_for_expected_answers == True:                                
                    number_of_expected_answers -= 1
                    if number_of_expected_answers == 0:
                        break
    
                remaining_time -= time.time() - start_time


            # react in iteration end:             
            self.on_iteration_end()
                      
            if retries > 0:
                retries -=1

        # return final processing        
        return self.on_loop_end()

        if isinstance(self._expected_answers,list) and self._check_automation:
            check_result = self.check_against_automation(list(result[0].keys()))        
        return result

    def check_against_automation(self, my_ccan_addresses):
        # check whether controllers have responded which do not to the automation:        
        controller_names = self._base.get_controller_names()     
        correct_answers = [False]*len(controller_names)

        unexpected = []
        for ccan_address in my_ccan_addresses:
            try:
                name = self._base.get_controller_name(ccan_address)
                correct_answers[controller_names.index(name)] = True
            except ValueError:
                unexpected.append(ccan_address)
        
        missing = []
        if False in correct_answers:
            
            for answer, name in zip(correct_answers, controller_names):
                if answer == False:
                    missing.append(name)            
        
        if len(missing) > 0:
            Report.print(ReportLevel.WARN,"The following controller(s) did not answer: " + str(missing) + ".\n")
        if len(unexpected) > 0:
            Report.print(ReportLevel.WARN,"The following controller(s) could not be matched to the automation:  " + str(unexpected) + ".\n")

        if len(missing) + len(unexpected) == 0:            
            Report.print(ReportLevel.VERBOSE,"Received successful result from all controllers of the automation.\n")
        
        return missing, unexpected

    def on_interrupt(self,my_signal, frame):
        Report.print(ReportLevel.WARN,"\nInterrupted.")
        