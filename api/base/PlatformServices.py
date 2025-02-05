import os
from src.base.CCAN_Error import CCAN_Error, CCAN_ErrorCode
from datetime import date


class PlatformServices:
    @staticmethod
    def uuid_to_string(my_uuid):
        result = ""
        result += "0x"
        for element in my_uuid:
            result += "{0:#0{1}x}".format(element, 4)[2:4]
        return result

    @staticmethod
    def convert_uuid_string_to_int_list(my_uuid_string):
        return list(
            map(
                lambda x: int(x, 16),
                [my_uuid_string[i : i + 2] for i in range(0, len(my_uuid_string), 2)],
            )
        )

    @staticmethod
    def are_versions_compatible(my_version1, my_version2):
        # major version differ -> not compatible
        if my_version1[0] != my_version2[0]:
            return False

        return True

    @staticmethod
    def determine_base_config_file_from_configuration_files(
        my_configuration_files, my_paths
    ):
        if len(my_configuration_files) < 2:
            return None

        while True:
            try:
                my_configuration_files.remove("")
            except ValueError:
                break

        prefix = os.path.commonpath(my_configuration_files)
        if len(prefix) < 0:
            raise CCAN_Error(
                CCAN_ErrorCode.COMMON_AUTOMATION_NOT_AVAILABLE,
                str(len(my_configuration_files))
                + " controllers have responded. The configurations have no common starting base in their names : "
                + str(my_configuration_files + "\n"),
            )

        # isolate common file name part and ending:
        filenames = []
        for file in my_configuration_files:
            filenames.append(file[len(prefix) + 1 : -len("_CONFIG_ENGINE.bin")])

        common_prefix = os.path.commonprefix(filenames)[:-1]
        #configuration_file = locateFile(common_prefix + ".pkl", my_paths, True)

        # omit ending:  '.pkl'
        return common_prefix

    @staticmethod
    def create_log_filename(my_log_filename):
        current_name = my_log_filename + "_current.log"
        rotation_filename = (
            my_log_filename + "_" + date.today().strftime("%d.%m.%Y") + ".log"
        )
        return current_name, rotation_filename
