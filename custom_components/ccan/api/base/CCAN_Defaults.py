import binascii
import pickle


# from api.PyCCAN_Compiler import Compiler


class CCAN_Defaults:
    def __init__(self):
        self.__resolver = None
        self.__init = False
        self.__text = None
        self.__maps = None

    def init_from_resolver(self, my_resolver):
        self.__resolver = my_resolver
        self.__init = True

    def init_from_pkl(self, my_file):
        with open(my_file + ".pkl", "rb") as f:
            self.__maps = pickle.load(f)
        self.__init = True

    @staticmethod
    def get_configuration_file_name(my_config_file, my_controller_name):
        try:
            return my_config_file + "_" + my_controller_name + "_ENGINE_CONFIG.bin"
        except TypeError:
            print(f"{my_config_file}  - {my_controller_name} TypeError Gotcha!")

    def get_map(self, my_key):
        if self.__init == False:
            return None
        return self.__maps[my_key]

    def update_maps(self):
        if self.__init == False:
            return None

        self.__maps = {}

        (map, title) = self.__get_controller_crc_map()
        self.__maps[title] = map

    def get_map(self, my_map_name):
        return self.__maps[my_map_name]

    def get_default_attribute(self, my_map_name, my_entry):
        return self.__maps[my_map_name][my_map_name + "_" + my_entry]

    def __get_controller_crc_map(self):
        if self.__init == False:
            return None

        controller_map = {}
        map_name = "CONTROLLER_CRC_LIST"
        header = {}
        header["FIRMWARE"] = 0x12345678
        header["BOOTLOADER"] = 0x2947F3B2
        header["BOOTLOADER_UPDATER"] = 0x87654321
        header["CONFIGURATION"] = 0xF03C2C95

        app_dict = self.__resolver.get_description_dictionary()["APP"]
        for id, entry in app_dict:
            if entry.get_type() == "CONTROLLER":
                for header_entry in header:
                    name = map_name + "_" + entry.get_name() + "_" + header_entry
                    controller_crc = binascii.crc32(name.encode("utf8"))
                    header_and_crc = (header[header_entry] << 32) + controller_crc
                    controller_map[name] = header_and_crc
        return (controller_map, map_name)

    def get_controller_from_crc(self, my_crc):
        match = False
        map = self.__maps["CONTROLLER_CRC_LIST"]
        for key in list(map.keys()):
            entry = map[key]
            if entry == my_crc:
                name = key[len("CONTROLLER_CRC_LIST") + 1 : key.rfind("_")]
                return name
        raise ValueError

    def create_defines_from_maps(self):
        self.__text = []
        text = ""
        for title in self.__maps:
            my_map = self.__maps[title]

            text += "/* " + title + " */\n"
            # detect element with largest length:
            adjust_length = 0
            for element in my_map:
                if len(element) > adjust_length:
                    adjust_length = len(element)

            for element in my_map:
                added_text = (
                    "#define "
                    + element.ljust(adjust_length)
                    + " "
                    + str(hex(my_map[element]))
                    + "\n"
                )
                text += added_text
        self.__text.append(text)

    def write_defines_to_file(self, my_file):
        if self.__text is None:
            return

        file = open(my_file + ".h", "w")
        for block in self.__text:
            file.write(block)
            file.write("\n")
        file.close()

    def write_python_maps_to_file(self, my_file):
        with open(my_file + ".pkl", "wb") as f:
            pickle.dump(self.__maps, f, pickle.HIGHEST_PROTOCOL)
