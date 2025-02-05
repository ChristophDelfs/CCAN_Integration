class TimeDelta():
    def __init__(self,my_seconds):
        self.__min = int(my_seconds / 60)
        self.__sec = my_seconds - self.__min*60

    def __str__(self):
        """returns time delta nicely formatted

        Returns:
            _string: in the format "000 min :: 00.00 sec"
        """
        #if self.__min == 0:
        #    return "{:04.2f}".format(self.__sec)+ " sec"
        return "{:02d}".format(self.__min) + ":" + "{:05.2f}".format(self.__sec)        


