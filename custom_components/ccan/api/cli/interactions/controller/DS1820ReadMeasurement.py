from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DS1820ReadMeasurement(Interaction): 
    def __init__(self, my_connector, my_retries, my_pin, my_romcode):    
        super().__init__(my_connector, my_retries)
        self._pin = my_pin
        self._romcode =  int(my_romcode,16)
        
    def do(self):        
        # defaults:
        self.set_request(f"DS1820_SERVICE::DS1820_SERVICE_GET_LAST_TEMPERATURE({self._pin}, {self._romcode})")
        self.set_expected_answers( ["DS1820_SERVICE::DS1820_SERVICE_GET_LAST_TEMPERATURE_REPLY()","DS1820_SERVICE::DS1820_SERVICE_PIN_NOT_AVAILABLE()","DS1820_SERVICE::DS1820_SERVICE_RESULT_CODE()"])          
        return super().do()

    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          

        if my_index == 2:
            error_code = my_received_event.get_parameters().get_values()[0]       
            raise  CCAN_Error(CCAN_ErrorCode.DS1820_SENSING_ERROR,f"Failure code: {error_code}")  

        if my_index == 1:
            raise  CCAN_Error(CCAN_ErrorCode.DS1820_PIN_NOT_AVAILABLE)
   
        (self._temperature, self._scratch_pad) = my_received_event.get_parameter_values()
        return self._temperature, self._scratch_pad

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):           
        Report.print(ReportLevel.VERBOSE,f"Measured temperature is {self._temperature if self._temperature != 85 and self._temperature < 4095 else "invalid"}.\nScratch pad content is {self._scratch_pad}.\n")          
        return True
