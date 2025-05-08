from api.cli.interactions.Interaction import Interaction
from api.base.Report import Report, ReportLevel
from api.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode

class DetectDS1820(Interaction): 
    def __init__(self, my_connector, my_retries, my_pin):    
        super().__init__(my_connector, my_retries)
        self._pin = my_pin

    def do(self):        
        self.set_request("DS1820_SERVICE::DS1820_SERVICE_SEARCH("+str(self._pin)+")")
        self.set_expected_answers( ["DS1820_SERVICE::DS1820_SERVICE_SEARCH_RESULT()",
            "DS1820_SERVICE::DS1820_SERVICE_DETECTION_ERROR()",
            "DS1820_SERVICE::DS1820_SERVICE_PIN_NOT_AVAILABLE()"])
        return super().do()
    
    def before_send(self):
        return

    def on_receive(self,my_received_event, my_index):          
                                                    
        if my_index == 1:             
            error_code = my_received_event.get_parameters().get_values()[0]
            if error_code == 1:
                raise CCAN_Error(CCAN_ErrorCode.DS1820_GND_AND_DATA_ARE_CONNECTED)
            elif error_code == 2:
                raise  CCAN_Error(CCAN_ErrorCode.DS1820_NO_SENSOR_DETECTED)
            elif error_code > 2:
                raise  CCAN_Error(CCAN_ErrorCode.DS1820_SENSING_ERROR)                 
            
        if my_index == 2:
            raise  CCAN_Error(CCAN_ErrorCode.DS1820_PIN_NOT_AVAILABLE)

        # evaluate answer:
        self._detected_sensors      = my_received_event.get_parameters().get_values()[0]
        self._detected_power_supply = my_received_event.get_parameters().get_values()[1]

        return True

    def on_receive_failure(self, my_exception):
        raise my_exception

    def on_iteration_end(self):
        return

    def on_loop_end(self):    

        number_of_detected_devices = len(self._detected_sensors)
                                
        if number_of_detected_devices > 0:
            print(str(number_of_detected_devices) + (" device" if len(self._detected_sensors) == 1 else " devices" + " detected at pin " + str(self._pin) + ":"))
         
            for element, i in zip(self._detected_sensors, range(1,len(self._detected_sensors)+1)): 

                hex_value = hex(element)   
                type_info_number = element  & 255
                if type_info_number == 0x28:
                    type_info ="DS18B20"
                elif type_info_number == 0x10:
                    type_info = "DS1820 "
                elif type_info_number == 0x22:
                    type_info = "DS1822 "
                else:
                    type_info = "Invalid Type"
                    
                Report.print(ReportLevel.VERBOSE,"# "+ str(i) + ":  Typ " + type_info + " with ROM Address " +  hex_value + "\n")
     
        if self._detected_power_supply == 0:
            power_supply_type = " parasite"
        elif self._detected_power_supply == 1:
            power_supply_type = " dedicated"
        else:
            power_supply_type = "n unknown"

        Report.print(ReportLevel.VERBOSE,f'Sensor{"s are" if number_of_detected_devices> 1 else " is"} powered by a{power_supply_type} power_supply.\n')

        return self._detected_sensors, self._detected_power_supply
