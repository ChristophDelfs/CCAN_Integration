from src.cli.interactions.Interaction import Interaction
from src.base.Report import Report, ReportLevel
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DS1820RequestMeasurement(Interaction): 
    def __init__(self, my_connector, my_retries, my_pin, my_romcode):    
        super().__init__(my_connector, my_retries)
        self._pin = my_pin
        self._romcode =  int(my_romcode,16)

    def do(self):        
        self.set_request(f"DS1820_SERVICE::DS1820_SERVICE_REQUEST_INSTANT_MEASUREMENT({self._pin}, {self._romcode})")
        self.set_expected_answers( ["DS1820_SERVICE::DS1820_SERVICE_RESULT_CODE()","DS1820_SERVICE::DS1820_SERVICE_PIN_NOT_AVAILABLE()"])          
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          

        if my_index == 1:
            raise  CCAN_Error(CCAN_ErrorCode.DS1820_PIN_NOT_AVAILABLE)
                                                     
        if my_index == 0:             
            error_code = my_received_event.get_parameters().get_values()[0]          
            if error_code > 0:
                raise  CCAN_Error(CCAN_ErrorCode.DS1820_SENSING_ERROR,f"Failure code: {error_code}")                             
       

        return True

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):    
        Report.print(ReportLevel.VERBOSE,"Measurement triggered.\n")          
        return True
