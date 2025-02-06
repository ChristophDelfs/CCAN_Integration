from api.cli.interactions.automation.AutomationInteraction import AutomationInteraction

from api.base.PlatformServices import PlatformServices
from api.base.PlatformDefaults import PlatformDefaults
from api.base.Report import Report, ReportLevel
import time
import signal

class AutomationPing(AutomationInteraction): 
    def __init__(self, my_connector, my_waiting_time,  my_number_of_pings,my_ping_delay,  my_automation_file):         
        super().__init__(my_connector, my_waiting_time, my_number_of_pings, my_automation_file)   
        signal.signal(signal.SIGINT, self.on_interrupt)            
       
        self._count = {}        
        self._average_roundtrip_time = {}
        self._ping_delay = my_ping_delay
        self._connect = my_connector
        self._number_of_pings = my_number_of_pings
        self._waiting_time = my_waiting_time
        
    def do(self):        
        self.set_request("LIFE_SERVICE::PING()")
        self.set_expected_answers(["LIFE_SERVICE::PONG()"])

        self._iteration_count = 0

        super().do(collect_answers= False)

    def before_send(self):
        self._send_time_stamp = time.time()
       

    def on_receive(self,my_received_event, my_index):
        ccan_address = my_received_event.get_sender_address()
        self._roundtrip_time = my_received_event.get_time_stamp()- self._send_time_stamp           

        try:          
            self._average_roundtrip_time[ccan_address] = (self._average_roundtrip_time[ccan_address] * self._count[ccan_address] + self._roundtrip_time) / (self._count[ccan_address] +1)
            self._count[ccan_address] += 1
        
        except KeyError:
            self._count[ccan_address] = 1
            self._average_roundtrip_time[ccan_address] = self._roundtrip_time           

        #print("Address " + str(ccan_address) + " Start time : " + str(self._send_time_stamp) + "   current roundtrip time:  " + str(self._roundtrip_time) + "    counts = " + str(self._count[ccan_address]))
        
        return False  

    def on_iteration_end(self):     
        self._iteration_count += 1
        Report.print(ReportLevel.VERBOSE,'{:>7}'.format(self._iteration_count) + " answers from " +'{:>2}'.format(len(self._count)) + " controllers..",my_rewind_flag = True)
        time.sleep(self._ping_delay)

    def on_loop_end(self):                  
        return self.get_result()
  
    def get_result(self):
        self._losses = {}
        for receiver in self._count:
            self._losses[receiver] = self._iteration_count - self._count[receiver]
        return (self._count, self._losses, self._average_roundtrip_time)          


    def on_interrupt(self,my_signal, frame):       
        self.terminate_loop()           
        time.sleep(2*self._ping_delay + self._waiting_time)
        counts ,losses, average_roundtrip_times = self.get_result()
        print("\n")

        receivers = list(counts)
        receivers.sort()
       
        if len(receivers)  == 0:
            Report.print(ReportLevel.VERBOSE,"No responses at all.\n")     
            return 

        Report.print(ReportLevel.VERBOSE,f"{'Controller:':30}" +  f"{'Address':10}" +  f"{'Average Response Times':25}" +   f"{'Losses':20} \n")
        for receiver in receivers:
            # Print results:          
            name = self._base.get_controller_name(receiver)
            Report.print(ReportLevel.VERBOSE,f"{name:30}" +  '{:<10}'.format(receiver)  + f"{' ':6}"+ '{:5.2f}'.format(average_roundtrip_times[receiver]*1000)+"ms" f"{' ':12}" + str(0 if losses[receiver] < 0 else losses[receiver]) + "\n")     



      