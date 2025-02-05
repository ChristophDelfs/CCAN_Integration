from src.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from src.base.Report import ReportLevel, Report
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
import time

class BroadcastPing(BroadcastInteraction): 
    def __init__(self, my_connect, my_waiting_time, my_number_of_pings, my_ping_delay): 
        
        super().__init__(my_connect, my_waiting_time, my_number_of_pings)
        self._count = {}        
        self._average_roundtrip_time = {}
        self._ping_delay = my_ping_delay
        self._connect = my_connect
        self._number_of_pings = my_number_of_pings
        self._waiting_time = my_waiting_time
        
    def do(self):           
        self.set_request("LIFE_SERVICE::PING()")
        self.set_expected_answers(["LIFE_SERVICE::PONG()"])

        self._iteration_count = 0

        return super().do()

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
        return False  

    def on_iteration_end(self):     
        if len(self._count) == 0:
            raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)

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

        Report.print(ReportLevel.VERBOSE,"Average Response Times:\n")
        for receiver in sorted(list(receivers)):
            # Print results:          
            Report.print(ReportLevel.VERBOSE,'Controller with address {:>5}'.format(receiver) + ":  " +  '{:5.2f}'.format(average_roundtrip_times[receiver]*1000)+"ms  (" + str(0 if losses[receiver] < 0 else losses[receiver]) + " losses)\n")     
       

