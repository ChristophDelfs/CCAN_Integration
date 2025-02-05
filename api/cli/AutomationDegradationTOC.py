from src.resolver.Definitions import ElementTypes
from src.base.PlatformDefaults import PlatformDefaults
from collections import namedtuple


class AutomationDegradationTOC:
    DegradedElement = namedtuple(
        "DegradedElement",
        "board_address board_name connection name type status_explanation code_explanation",
    )
    DegradationStatusExplanation = ["Not degraded", "Degradation_source", "Degraded"]

    def __init__(self, my_description_dict, my_instance_dict):
        self.__description_dictionary = my_description_dict
        self.__instance_dictionary = my_instance_dict
        self.__toc = []

    def insert(self, ccan_address, input):
        self.__toc.append(
            self.__resolve_element(ccan_address, input[0], input[1], input[2], input[3])
        )

    def __resolve_instance_by_ccan_address(self, address):
        apps = self.__instance_dictionary["APP"]

        if address == PlatformDefaults.SERVER_CCAN_ADDRESS:
            return None, None, "CCAN Server"

        if address == PlatformDefaults.INVALID_CCAN_ADDRESS:
            return None, None, "UNCONFIGURED CLIENT"

        if address == PlatformDefaults.BROADCAST_CCAN_ADDRESS:
            return None, None, "BROADCAST"

        try:
            for id, app in apps:
                for parameter in app.get_description_list("PARAMETER"):
                    if str(parameter.get_format()) == "CCAN_ADDRESS":
                        if parameter.get_value() == address:
                            return (id, app, app.get_name())
        except Exception:
            pass

        return "Instance (" + str(address) + ")"

    def __resolve_element(
        self, from_instance, my_element_id, my_element_type, my_status, my_code
    ):
        element_code_explanation = "Unknown explanation"
        connection_name = ""
        element_name = ""
        element_type = ""
        element_status_explanation = ""

        # check whether controller app needs to be found first:
        if ElementTypes[my_element_type] != "DEVICE":
            app_id, app, app_name = self.__resolve_instance_by_ccan_address(
                from_instance
            )

        if my_element_type >= len(ElementTypes):
            raise AttributeError

        if ElementTypes[my_element_type] == "DEVICE":
            device_dictionary = self.__instance_dictionary["DEVICE"]
            for id, device in device_dictionary:
                if id == my_element_id:
                    element_type = device.get_type()
                    element_name = device.get_name()
                    connection_name = app_name
                    # element_connection_name = "pin name" # dev.connection_set[0].pin_name

                    # get degradation description:
                    device_type = self.__description_dictionary[
                        "DEVICE"
                    ].get_entry_by_name(element_type)
                    degradation_dictionary = device_type.get_description_list(
                        "DEGRADATION"
                    )

                    if my_code == 0:                     
                        element_code_explanation = ""
                    else:
                        descriptors = self.__description_dictionary["DEVICE"]
                        element_descriptor = descriptors.get_entry_by_name(element_type)
                        try:
                            degradation_dictionary = (
                                element_descriptor.get_description_list("DEGRADATION")
                            )
                        except KeyError:
                            element_status_explanation = (
                                AutomationDegradationTOC.DegradationStatusExplanation[
                                    my_status
                                ]
                            )
                            break

                        element_status_explanation = (
                            AutomationDegradationTOC.DegradationStatusExplanation[
                                my_status
                            ]
                        )
                        element_code_explanation = (
                            degradation_dictionary.get_entry_by_id(my_code-1)
                        )
                        break

        if ElementTypes[my_element_type] == "APPLICATION":
            dictionary = self.__instance_dictionary["APP"]
            for id, global_app in dictionary:
                if (
                    global_app.get_id() == my_element_id
                    and global_app.get_controller_name() == app.get_name()
                ):
                    element_name = global_app.get_name()
                    element_type = global_app.get_type()
                    connection_name = app.get_controller_name()


                    # get app degradation description:
                    descriptors = self.__description_dictionary["APP"]
                    element_descriptor = descriptors.get_entry_by_name(element_type)
                    try:
                        degradation_dictionary = (
                            element_descriptor.get_description_list("DEGRADATION")
                        )
                    except KeyError:
                        element_status_explanation = (
                            AutomationDegradationTOC.DegradationStatusExplanation[
                                my_status
                            ]
                        )
                        break

                    element_status_explanation = (
                        AutomationDegradationTOC.DegradationStatusExplanation[
                            my_status
                        ]
                    )
                    element_code_explanation = (
                        degradation_dictionary.get_entry_by_id(my_code-1)
                    )
                    break

        if ElementTypes[my_element_type] == "DRIVER":
            return self.resolve_degraded_sensor_driver(
                app, from_instance, my_element_id, my_element_type, my_status, my_code
            )

        if ElementTypes[my_element_type] == "TRANSPORT_ADAPTER":
            dictionary = app.get_description_list("TRANSPORT_ADAPTER")
            for id, driver in dictionary:
                if id == my_element_id:
                    element_type = driver.get_type()
                    element_name = driver.get_name()
                    connection_name = app_name
               
                    # element_connection_name = "pin name" # dev.connection_set[0].pin_name

                    # degradation_list = sensor.driver_instance.parsed_element.degradation_description_list
                    if my_code == 0:
                        element_status_explanation = "OK"
                        element_code_explanation = ""
                    else:
                        descriptors = self.__description_dictionary["TRANSPORT_ADAPTER"]
                        element_descriptor = descriptors.get_entry_by_name(element_type)
                        try:
                            degradation_dictionary = (
                                element_descriptor.get_description_list("DEGRADATION")
                            )
                        except KeyError:
                            element_status_explanation = (
                                AutomationDegradationTOC.DegradationStatusExplanation[
                                    my_status
                                ]
                            )
                            break

                        element_status_explanation = (
                            AutomationDegradationTOC.DegradationStatusExplanation[
                                my_status
                            ]
                        )
                        element_code_explanation = (
                            degradation_dictionary.get_entry_by_id(my_code-1)
                        )
                        break

        if ElementTypes[my_element_type] == "COMMUNICATION_DRIVER":
            dictionary = app.get_description_list("COMMUNICATION_DRIVER")
            for id, driver in dictionary:
                if id == my_element_id:
                    element_type = driver.get_type()
                    element_name = driver.get_name()
                    connection_name = app_name

                    # degradation_list = sensor.driver_instance.parsed_element.degradation_description_list
                    if my_code == 0:
                        element_status_explanation = "OK"
                        element_code_explanation = ""
                    else:
                        descriptors = self.__description_dictionary[
                            "COMMUNICATION_DRIVER"
                        ]
                        element_descriptor = descriptors.get_entry_by_name(element_type)
                        try:
                            degradation_dictionary = (
                                element_descriptor.get_description_list("DEGRADATION")
                            )
                        except KeyError:
                            element_status_explanation = (
                                AutomationDegradationTOC.DegradationStatusExplanation[
                                    my_status
                                ]
                            )
                            break

                        element_status_explanation = (
                            AutomationDegradationTOC.DegradationStatusExplanation[
                                my_status
                            ]
                        )
                        element_code_explanation = (
                            degradation_dictionary.get_entry_by_id(my_code-1)
                        )
                        break

        degraded_element = AutomationDegradationTOC.DegradedElement(
            board_address=from_instance,
            board_name=app_name,
            connection=connection_name,
            name=element_name,
            type=element_type,
            status_explanation=element_status_explanation,
            code_explanation=element_code_explanation,
        )
        return degraded_element

    def resolve_degraded_sensor_driver(
        self,
        my_controller,
        from_instance,
        my_element_id,
        my_element_type,
        my_status,
        my_code,
    ):
        for app in self.get_connected_applications(my_controller):
            app_dictionary = app.get_description_list("SENSOR_DRIVER")
            app_description = self.__description_dictionary["APP"].get_entry_by_name(
                app.get_type()
            )
            for id, driver in app_dictionary:
                if id == my_element_id:
                    element_type = driver.get_type()
                    element_name = driver.get_name()
             
                    # degradation_list = sensor.driver_instance.parsed_element.degradation_description_list
                    if my_code == 0:
                        element_status_explanation = "OK"
                        element_code_explanation = ""
                    else:
                        descriptors = self.__description_dictionary["SENSOR_DRIVER"]
                        element_descriptor = descriptors.get_entry_by_name(element_type)
                        try:
                            degradation_dictionary = (
                                element_descriptor.get_description_list("DEGRADATION")
                            )
                            element_status_explanation = (
                                AutomationDegradationTOC.DegradationStatusExplanation[
                                    my_status
                                ]
                            )
                            element_code_explanation = (
                                degradation_dictionary.get_entry_by_id(my_code-1)
                            )
                            if  element_code_explanation  is None:
                                element_code_explanation = ""
                        except KeyError:
                            element_status_explanation = (
                                AutomationDegradationTOC.DegradationStatusExplanation[
                                    my_status
                                ]
                            )
                            element_code_explanation = ""

                    # connection:
                    connection = driver.get_description_list("CONNECTION")[0]

                    degraded_element = AutomationDegradationTOC.DegradedElement(
                        board_address=from_instance,
                        board_name=my_controller.get_name(),
                        connection=app.get_name()
                        + "::"
                        + app_description.get_description_list(
                            "SENSOR_DRIVER"
                        ).get_names_as_list()[connection.get_pin_id()],
                        name=element_name,
                        type=element_type,
                        status_explanation=element_status_explanation,
                        code_explanation=element_code_explanation,
                    )

                    return degraded_element
        # shall not happen: could not find sensor driver in dict's
        raise ValueError

    def get_connected_applications(self, my_app):
        result_list = []

        for id, app in self.__instance_dictionary["APP"]:
            if app.get_controller_name() == my_app.get_controller_name():
                result_list.append(app)

        return result_list

    ## iterator ##

    def __iter__(self):
        self.__toc = sorted(self.__toc, key=self._sorted_key)
        self._iteration_index = 0
        return self

    def __next__(self):
        if self._iteration_index == self.get_size():
            raise StopIteration

        result = self.__toc[self._iteration_index]
        self._iteration_index += 1
        return result

    def get_size(self):
        return len(self.__toc)

    def _sorted_key(self, my_element):
        return (my_element.type, my_element.name)

    # def print(self):
    #    if bool(self.__toc):
    #        print('\033[1m' + f'{"Typ":11}', f'{"Name":10}', f'{"Controller::Connection":25}' + f'{"DEGRADATION STATUS":15}', "     ", f'{"CODE":15}' + "  (" + "EXPLANATION" + ")" + '\033[0m')
    #        for degraded_element in self.__toc:
    #            print(f'{degraded_element.type:20}', f'{degraded_element.name:20}', f'{"on " + degraded_element.connection  + " is ":25}' + f'{degraded_element.status_explanation:15}', " : " + degraded_element.code_explanation)
    #    else:
    #        print("No degradations reported. All fine!")


#     # https://stackoverflow.com/questions/8924173/how-do-i-print-bold-text-in-python
# print('\033[1m' + f'{"Typ":11}', f'{"Description":20}', f'{"Name":10}', f'{"Controller::Connection":25}' + f'{"DEGRADATION STATUS":15}', "     ", f'{"CODE":15}' + "  (" + "EXPLANATION" + ")" + '\033[0m')
