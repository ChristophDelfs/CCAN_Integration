from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class InitializeExpander(Interaction): 
    def __init__(self, my_connector, my_retries, my_i2c_address, my_name, my_expander_type):    
        super().__init__(my_connector, my_retries)

        if my_i2c_address < 0 or my_i2c_address > 3:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_ARGUMENT," I2C address must be in the range 0..3")
        self._i2c_address = my_i2c_address      


        if len(my_name) > 49:
            my_name = my_name[0:49]                  
            Report.print(ReportLevel.WARN,"Expander name shortened to :" + my_name + ".\n")
        self._name = my_name

        expander_types = { "Input":1, "Output": 2}     
        try:
            self._expander_type = expander_types[my_expander_type]
        except  KeyError:
            raise CCAN_Error(CCAN_ErrorCode.ILLEGAL_EXPANDER_TYPE, str(my_expander_type))       

    def do(self):        
        self.set_request("EXPANDER_SERVICE::INITIALIZE_EXPANDER32("+str(self._i2c_address)+"," + str(self._expander_type)+ "," + str(self._name) + ")")
        self.set_expected_answers( ["EXPANDER_SERVICE::ACCESS_OK()","EXPANDER_SERVICE::ACCESS_ERROR()"])
        return super().do()
    
    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
        if my_index == 1:           
            raise CCAN_Error(CCAN_ErrorCode.EXPANDER_INITIALIZATION_FAILED," Access failed at address " + str(self._i2c_address) + ".")          
        Report.print(ReportLevel.VERBOSE,"Expander successfully initialized.\n")
        return True

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):           
        return True    
    
