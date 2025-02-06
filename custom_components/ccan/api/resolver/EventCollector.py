from api.resolver.ResolverError import ResolverError
import copy
import queue


class EventCollectorFactory:
    def create_event_collectors_from_event(my_event, my_instance_dictionary):
        new_collector = EventCollector()
        new_collector.collect(my_event, my_instance_dictionary)
        return new_collector


    def create_sliced_event_collector(my_event,my_parameter_collector):
        new_collector = EventCollector()
        new_collector.__result_events = [copy.deepcopy(my_event)]
        new_collector.__result_collectors = my_parameter_collector
        return new_collector

    def create_collector_from_event_and_parameters(my_event,*my_parameters):
        #new_collector = EventCollector()
        result_collector = queue.Queue()

        for my_parameter in my_parameters:
            result_collector.put(my_parameter)
        return result_collector


class EventCollector:
    def __init__(self):
        pass

    def get_next_parameters(self):
        if self.__result_collectors[0].empty():
            raise ValueError
        return self.__result_collectors[0].get()
    
    def get_events(self):
        return self.__result_events

    def __iter__(self):
        self.__current = 0
        return self

    def  __next__(self):
        if self.__current == len(self.__result_collectors):
            raise StopIteration

        self.__current +=1

        # prepare a copy of the selected collector:
        result_queue = EventCollector.copy_queue(self.__result_collectors[self.__current-1])

        return self.__result_events[self.__current-1], result_queue

    def collect(self,my_event, my_instance_dictionary):          
        self.__result_events, self.__result_collectors = self.__collect(my_event,my_instance_dictionary)


    def __collect(self,my_event, my_instance_dictionary):        
        result_events    =  []
        result_collectors = []
     
        start_parameters = my_event.get_description_list("PARAMETER")

        [device_name, id] = my_event.get_description_list("EVENT_PATH")
        if my_event.is_template():             
            # collect alias events for the template related to this mapping:          
            template      = my_instance_dictionary.get_entry_by_name(device_name)
            alias_map     = template.get_description_list("ALIAS_EVENTS")
            try:
                alias_mappings  = alias_map.get_by_name(my_event.get_name())
            except KeyError:
                raise ResolverError(my_event.get_location(), "Either template definition does not cover defined event " + my_event.get_name() + " or this event simply does not exist.")   
                    
            for alias_event_pair in alias_mappings:   

                # get alias events and parameter "stack":
                alias_event = alias_event_pair.get_target_event()
                resolved_alias_events, collectors = self.__collect(alias_event, my_instance_dictionary)
                   

                # add to existing collector list:
                result_collectors.extend(collectors)

                # and event list:
                result_events.extend(resolved_alias_events)

            # add own parameter to queue:
            for collector in result_collectors:
                 collector.put(copy.deepcopy(start_parameters))

        else:
            if my_event is None:
                pass
            # plain event:
            result_collectors = [queue.Queue()]
            result_collectors[0].put(copy.deepcopy(start_parameters))
            result_events     = [ copy.deepcopy(my_event) ]          

        return result_events, result_collectors
    

    def copy_queue(my_queue):
        result_queue = queue.Queue()

        # empty queue:
        queue_list = []
        while my_queue.qsize() != 0:
            queue_list.append(my_queue.get())

        # refill queue:
        for entry in queue_list:
            my_queue.put(copy.deepcopy(entry))
            result_queue.put(copy.deepcopy(entry))

        return result_queue
