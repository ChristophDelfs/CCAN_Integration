class ResolvedBase:
    def __init__(self, my_name, my_location_info):
        self.__location_info = my_location_info
        self.__name = my_name

    def get_name(self):
        return self.__name

    def get_location(self):
        return self.__location_info