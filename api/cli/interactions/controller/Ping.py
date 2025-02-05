from src.cli.interactions.Interaction import Interaction
from src.base.Report import Report, ReportLevel
import time
import signal

class Ping(Interaction): 
    def __init__(self, my_connector, my_number_of_pings, my_ping_delay): 
        
        super().__init__(my_connector, my_number_of_pings)
        self.__count = 0
        self.__losses = 0 
        self.__average_roundtrip_time = 0         
        self.__ping_delay = my_ping_delay
        self.__connector = my_connector
        self.__number_of_pings = my_number_of_pings
        signal.signal(signal.SIGINT, self.on_interrupt)           

        self.__roundtrip_time = 0
        self.__average_roundtrip_time = 0
        
    def do(self):
        self.set_request("LIFE_SERVICE::PING()")
        self.set_expected_answers(["LIFE_SERVICE::PONG()"])

        super().do()

    def before_send(self):
        self.__send_time_stamp = time.time()

    def on_receive(self,my_received_event, my_index):
        self.__roundtrip_time = my_received_event.get_time_stamp()- self.__send_time_stamp                          

        self.__average_roundtrip_time *=self.__count
        self.__average_roundtrip_time += self.__roundtrip_time

        self.__count += 1
        self.__average_roundtrip_time /= self.__count      
        return False  

    def on_receive_failure(self, my_exception):       
        Report.print(ReportLevel.VERBOSE,'{:>7}'.format(self.__count+1) + " -> " + "loss    Average: " + '{:5.2f}'.format(self.__average_roundtrip_time*1000) + "ms" +   "     Losses "  + str(self.__losses) + " (" + str(round(self.__losses/self.__count*100)) + "%)      " if self.__count != 0 else "" ,my_rewind_flag = True)       
        self.__losses +=1
        self.__count += 1

    def on_iteration_end(self):     
        Report.print(ReportLevel.VERBOSE,'{:>7}'.format(self.__count+1) + " -> " + '{:5.2f}'.format(self.__roundtrip_time*1000) + "ms   Average: " + '{:5.2f}'.format(self.__average_roundtrip_time*1000) + "ms" +   "     Losses "  + str(self.__losses) +   " (" + str(round(self.__losses/self.__count*100)) + "%)     " ,my_rewind_flag = True)
        time.sleep(self.__ping_delay)

    def on_loop_end(self):     
        return (self.__count, self.__losses, self.__average_roundtrip_time)          

    def on_interrupt(self,my_signal, frame):       
        self.terminate_loop()   
        print("\n")
        return 

