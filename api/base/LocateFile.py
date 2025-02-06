import os
from pathlib import Path
from api.base.PlatformConfiguration import PlatformConfiguration


def locateFile(my_filename, my_path_list, recursive_search=False):
    if my_filename.startswith("/"):
        if os.path.isfile(my_filename):
            return my_filename
        else:
            raise FileNotFoundError

    path_list = []
    for directory in my_path_list:
        full_directory_path = str(Path(PlatformConfiguration.CCAN_PATH()) / directory)

        if recursive_search:
            path_list.extend(collect_path(full_directory_path))
        else:
            path_list.append(full_directory_path)

    for path in path_list:
        full_filename = os.path.join(path, my_filename)
        if os.path.isfile(full_filename):
            return full_filename

    # check current directory in any case:
    if os.path.isfile(os.path.join(os.getcwd(), my_filename)):
        return os.path.join(os.getcwd(), my_filename)

    raise FileNotFoundError


def collect_path(my_directory_path):
    path_list = [my_directory_path]

    try:
        directories = next(os.walk(my_directory_path))[1]
    except StopIteration:
        return []

    if directories != []:
        for directory in directories:
            new_directory = os.path.join(my_directory_path, directory)
            path_list.extend(collect_path(new_directory))
    return path_list
