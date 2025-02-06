class CCAN_Warnings():
    __warning_set = []
 
    def warn(my_location,my_message_text):     
        CCAN_Warnings.__warning_set.append([my_location,my_message_text])

             
    def show_all():
        for location, message_text in CCAN_Warnings.__warning_set:
            print(location.file + ":" +str(location.line)+":" +str(location.column) + " >> " + message_text)
 
        