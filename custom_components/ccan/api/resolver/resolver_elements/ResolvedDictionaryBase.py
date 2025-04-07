from ..ResolverError import ResolverError

class ResolvedDictionaryBase:
    def __init__(self, my_allowed_map, my_start_id=0):
        self.__current_id_counter = my_start_id
        self.__list_of_elements = {}
        self.__classes_map = my_allowed_map
        self.__entry_counter = 0

    def get_by_name(self, my_name):
        return self.__list_of_elements[my_name]

    def get_entry_by_name(self, my_name):
        (id, dict_element) = self.__list_of_elements[my_name]
        return dict_element

    def get_entry_by_id(self, my_id):
        for name in self.__list_of_elements:
            (id, dict_element) = self.__list_of_elements[name]
            if id == my_id:
                return dict_element
        return None

    def get_id_by_name(self, my_name):
        (id, dict_element) = self.__list_of_elements[my_name]
        return id

    def get_type_map(self):
        result_map = {}
        for element_name in self.__list_of_elements:
            (id, element) = self.__list_of_elements[element_name]
            result_map[element_name] = self.get_id_by_name(element_name)
        return result_map

    def is_supported_class(self, my_class):
        try:
            test = self.__classes_map[my_class]
            return True
        except KeyError:
            return False

    def insert(self, my_new_description, my_description_id=None):
        my_type = my_new_description.get_type()
        if self.__classes_map is not None:
            try:
                test = self.__classes_map[my_type]
            except KeyError:
                raise ResolverError(
                    my_new_description.get_location(),
                    f"New description for {my_new_description.get_type_name()} is not allowed. Available is a type within {self.__classes_map.keys()} .")


        if my_description_id is None:
            id = self.__current_id_counter
            self.__current_id_counter += 1
        else:
            id = my_description_id

        try:
            dummy = self.__list_of_elements[my_new_description.get_name()][1]
            raise ResolverError(
                my_new_description.get_location(),
                my_new_description.get_name()
                + " has been defined twice. Initially it has been defined in line "
                + str(dummy.get_location().line)
                + " of file "
                + dummy.get_location().file
                + ".",
            )
        except KeyError:
            pass

        self.__list_of_elements[my_new_description.get_name()] = (
            id,
            my_new_description,
        )
        self.__entry_counter += 1

        return (my_new_description.get_name(), id)

    def remove(self, my_description):
        try:
            del self.__list_of_elements[my_description.get_name()]
        except KeyError:
            raise ResolverError(
                my_description.get_location(),
                my_description.get_name()
                + " was attempted to be removed. But it does not exist. This is an internal error!",
            )

    def get_number_of_entries(self):
        return self.__entry_counter

    def add_class_element(self, my_class_element_name, my_class_element_id):
        self.__classes_map[my_class_element_name] = my_class_element_id

    # make it iterable:
    def __iter__(self):
        self.__iter_count = 0
        self.__iter_list = list(self.__list_of_elements.keys())
        return self

    def __next__(self):
        if self.__iter_count < len(self.__list_of_elements):
            result = self.__list_of_elements[self.__iter_list[self.__iter_count]]
            self.__iter_count += 1
            return result

        else:
            raise StopIteration