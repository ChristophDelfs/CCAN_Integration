class KeyMapBase:
    def __init__(self, my_key_map, my_key_name):
        self.__key_map = my_key_map
        test = self.__key_map[my_key_name]
        self.__key_name = my_key_name

    def __str__(self):
        return self.__key_name

    def get_key(self):
        return self.__key_map[self.__key_name]

    def get_key_format(self):
        from .ParameterFormat import ParameterFormat
        return ParameterFormat("UINT8")

    def get_list_of_types(self):
        return list(self.__key_map.keys())

    def get_map(self):
        return self.__key_map
