from flatten_dict import flatten


class ConfigurationManager():

    def __init__(self, my_description_dictionary):
        item_dictionary = {}
        for key in my_description_dictionary:
            item_dictionary[key] = my_description_dictionary[key].get_type_map()
           
        # creating hash:
        w = flatten(item_dictionary)
        hash_value = hash(frozenset(w))
        pass

            


   