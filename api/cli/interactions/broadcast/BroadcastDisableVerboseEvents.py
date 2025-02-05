from src.cli.interactions.broadcast.BroadcastInteraction import BroadcastInteraction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class BroadcastDisableVerboseEvents(BroadcastInteraction): 
    def __init__(self, my_connector, my_waiting_time, my_retries): 
        
        super().__init__(my_connector, my_waiting_time, my_retries)                      
        self._ack_received = {}
        
    def do(self):     
        self.set_request("ENGINE_SERVICE::DISABLE_VERBOSE_EVENTS()")
        self.set_expected_answers(["ENGINE_SERVICE::DISABLE_VERBOSE_EVENTS_ACK()"])
        super().do()

    def before_send(self):
        pass
       
    def on_receive(self,my_received_event, my_index):   
        ccan_address = my_received_event.get_sender_address()     
        self._ack_received[ccan_address] = True           
        return False  

    def on_iteration_end(self):     
        pass

    def on_loop_end(self):          
        if len(self._ack_received) > 0:
            Report.print(ReportLevel.VERBOSE,"Verbose events have been disabled on " + str(len(self._ack_received)) + " controllers:\n")
            for ccan_address in sorted(list(self._ack_received)):
                Report.print(ReportLevel.VERBOSE,"Controller with address " + str(ccan_address) +"\n")
        else:
             raise CCAN_Error(CCAN_ErrorCode.BROADCAST_NO_RESPONSE)           
        return (self._ack_received)  

