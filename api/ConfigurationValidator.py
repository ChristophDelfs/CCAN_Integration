#
#

from src.PyCCAN_Warnings import CCAN_Warnings


class ConfigurationValidator:
    # perform the configuration cleaning
    def do(my_resolver):
        ConfigurationValidator.remove_unused_sensor_drivers(
            my_resolver.resolver_store.get_instance_dictionary("APP")
        )

    def remove_unused_sensor_drivers(my_apps):
        for id, app in my_apps:
            removal_list = []
            # elicit all connected pins:
            connected_pins = app.get_description_list("SENSOR_DRIVER")
            for id, pin in connected_pins:
                if pin.is_not_used():
                    location_info = pin.get_location()
                    connection = pin.get_description_list("CONNECTION")[0]
                    removal_list.append(pin)
                    CCAN_Warnings.warn(
                        location_info,
                        "Sensor driver "
                        + connection.get_driver_name()
                        + " referenced as "
                        + connection.get_pin_name()
                        + " is not used by any device. The driver will be omitted in the configuration of controller "
                        + app.get_controller_name()
                        + ".",
                    )
            for unused_pin in removal_list:
                connected_pins.remove(unused_pin)

        return 0
