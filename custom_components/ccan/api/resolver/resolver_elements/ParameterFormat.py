from .KeyMapBase import KeyMapBase

class ParameterFormat(KeyMapBase):
    def __init__(self, my_format):
        Key = {}
        Key["BOOL"] = 0
        Key["UINT8"] = 1
        Key["UINT16"] = 2
        Key["UINT32"] = 3
        Key["UINT64"] = 4
        Key["INT8"] = 5
        Key["INT16"] = 6
        Key["INT32"] = 7
        Key["INT64"] = 8
        Key["FLOAT"] = 9
        Key["STRING"] = 10
        Key["NAME"] = 11
        Key["CCAN_ADDRESS"] = 20
        Key["IPV4_ADDRESS"] = 21
        Key["CONNECTION"] = 40        
        Key["DEVICE"] = 80

        super().__init__(Key, my_format)