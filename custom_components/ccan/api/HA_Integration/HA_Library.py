from api.base.PlatformDefaults import PlatformDefaults


class HA_Library:
    def __init__(self, my_connector):
        instance_dictionary = my_connector.get_instance_dictionary()
        self.__ha_devices = instance_dictionary["HOME_ASSISTANT_DEVICE"]
        self.connector = my_connector

    def get_devices(self, my_type) -> list:
        return [
            device for id, device in self.__ha_devices if device.get_type() == my_type
        ]

    def get_number_of_device_types(self):
        """Provide how many different HA device types are available in the automation."""
        type_map = {}
        result = 0
        for id, device in self.__ha_devices:
            new_type = device.get_type()
            try:
                type_map[new_type]
            except:
                type_map[new_type] = True
                result += 1
        return result

    def send(self, my_device, my_equivalent_name, *args):
        events = self.get_symbolic_event(my_device, my_equivalent_name, *args)
        for event in events:
            self.connector.send_event(event)
        return True

    def wait_for(self, delta, my_device, my_equivalent_name, *args):
        events = self.get_symbolic_event(my_device, my_equivalent_name, *args)
        event,idx = self.connector.wait_for_event_list(delta,events)
        return event



    def get_symbolic_event(self, my_device, my_equivalent_name, *args) -> str:
        prefix_map = my_device.get_description_list("EVENT_PREFIX_MAP")
        event_map = my_device.get_description_list("EQUIVALENT_MAP")
        prefixes = prefix_map[my_equivalent_name]
        events = event_map[my_equivalent_name]

        result = []

        for prefix, event in zip(prefixes, events):
            event_name = f"{prefix} {event.get_full_name()}("
            if len(args) > 0:
                for parameter in args:
                    event_name = f"{event_name} {parameter}, "
                event_name = event_name[:-2]
            event_name += ")"
            result.append(event_name)
        return result

    def get_equivalent(self, my_device, my_name):
        return my_device.get_description_list("EQUIVALENT_MAP")[my_name]

    def get_variable_value(self,  my_device, my_variable_name, my_delta):
        variable = self.get_equivalent(my_device, my_variable_name)
        # (full_name,variable_id) = connector.identify_variable(variable.get_name())
        variable_id = variable.get_id()
        self.connector.set_destination_address(PlatformDefaults.BROADCAST_CCAN_ADDRESS)
        assert self.connector.send_event(f"VARIABLE_SERVICE::GET({variable_id})")
        # check status
        while True:
            received_event = self.connector.wait_for_event(
                my_delta, "VARIABLE_SERVICE::GET_RESULT()"
            )
            parameters = received_event.get_parameter_values()
            if parameters[0] == variable_id:
                # print(f"Variable {my_variable_name}: {parameters[1]}")
                return parameters[1]

    def get_device_parameter_value(self, my_device, my_parameter_name):
        parameters = my_device.get_description_list("PARAMETER")
        for parameter in parameters:
            if parameter.get_name() == my_parameter_name:
                return parameter.get_value()
        raise KeyError
