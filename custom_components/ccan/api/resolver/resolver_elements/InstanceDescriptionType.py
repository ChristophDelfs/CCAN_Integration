from .KeyMapBase import KeyMapBase

class InstanceDescriptionType(KeyMapBase):
    def __init__(self, my_element):
        Key = {}
        Key["DEVICE"] = 0
        Key["VARIABLE"] = 1
        Key["SENSOR_DRIVER"] = 2
        Key["COMMUNICATION_DRIVER"] = 3
        Key["TRANSPORT_ADAPTER"] = 4
        Key["EVENT"] = 5
        Key["MAPPING"] = 6
        Key["PARAMETER"] = 7
        Key["CONNECTION"] = 8
        Key["DEGRADATION"] = 9
        Key["ATTRIBUTES"] = 10

        Key["AUTOMATION"] = 11
        Key["ALIAS_EVENTS"] = 12
        Key["ALIAS_VARIABLES"] = 13
        super().__init__(Key, my_element)
