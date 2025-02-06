from api.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastReset(BroadcastInteraction): 
    def __init__(self, my_cli, my_waiting_time, my_retries): 
        
        super().__init__(my_cli, my_waiting_time, my_retries)            
        self.__cli = my_cli
        self.__ack_received = []

        
    def do(self):     
        self.set_request("LIFE_SERVICE::RESET_REQUEST()")
        self.set_expected_answers(["LIFE_SERVICE::RESET_ACK()"])
        return super().do()

    def before_send(self):
        pass
       

    def on_receive(self,my_received_event, my_index):              
        ccan_address = my_received_event.get_sender_address()     
        self.__ack_received.append(ccan_address)            
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):     
        if len(self.__ack_received) > 0:
            Report.print(ReportLevel.VERBOSE,"Reset acknowledged by " + str(len(self.__ack_received)) + " controllers:\n")
            for ccan_address in sorted(list(self.__ack_received)):
                Report.print(ReportLevel.VERBOSE,"Controller with address " + str(ccan_address) +"\n")
        else:
             raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)           
        return (self.__ack_received)          

