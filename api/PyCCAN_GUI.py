'''
Created on 11.06.2018

@author: christoph
'''

import sys
import os
import PySimpleGUI as sg

class Gui:
    layout = [[sg.Text("Hold down a key")],
              [sg.Button("OK")]]
        
    layout = [ [sg.T('INPUT')],
               [ sg.Graph(canvas_size=(500, 60), graph_bottom_left=(0,0), graph_top_right=(500, 60), background_color='grey', key='input_graph')],
               [sg.T('OUTPUT')],
               [ sg.Graph(canvas_size=(500, 60), graph_bottom_left=(0,0), graph_top_right=(500, 60), background_color='grey', key='output_graph')],
               [ sg.T('Press buttons 0..9'), sg.Quit('Exit')]
               ]
    
    button_press_code = 100
    button_release_code = 101
    
    def __init__(self,destination,cli):
 
        self._window = sg.Window('PYCCAN GUI',return_keyboard_events=True, use_default_focus=False).Layout(Gui.layout).Finalize()
        for i in range (0,10):
            self._inputr(i)
            self._outputr(i)
            
        os.system('xset r rate 5 80')
        self._cli = cli
        self._destination = destination
        self._timeout = 0.01
    
    def _get_remote_status_update(self):
        try:
            app_event = self._cli.wait_for_application_event(self._timeout,self._destination, self._cli.get_own_address(),  "REMOTE_IO_SERVICE","OUTPUT_STATUS")
        except TimeoutError:
            return
        
        #print("Update received..")
        data = app_event.parameters[0].value
        length = len(data)
        # Remote Status update
        for i in range (length):
            if data[i] == 1:
                self._outputp(i)
            else:
                self._outputr(i)
    
    
    def _get_event_code(self,event):
        try: 
            code = int(event)
            if (code== 0):
                code = 10
            return code-1
        except ValueError:
            return -1
    
     
    def _inputp(self,n):
        self._window.FindElement('input_graph').DrawRectangle((10+50*n,50),(50*n+40,10),fill_color='green')
        
    def _inputr(self,n):
        self._window.FindElement('input_graph').DrawRectangle((10+50*n,50),(50*n+40,10),fill_color='white')
    
    def _outputp(self,n):
        self._window.FindElement('output_graph').DrawRectangle((10+50*n,50),(50*n+40,10),fill_color='green')
        
    def _outputr(self,n):
        self._window.FindElement('output_graph').DrawRectangle((10+50*n,50),(50*n+40,10),fill_color='red') 

    def do(self):
        
        event_list = [];
        counter = 0
        invalid_event_code = -1
        last_event_code = invalid_event_code
        while True:
            event, values = self._window.Read(10)
                    
            if event == "Exit":
                print("exiting")
                break
            if event == None:
                print("exiting")
                break;
            
            if last_event_code == invalid_event_code:
                if event is sg.TIMEOUT_KEY:
                    # ignore
                    event_code = invalid_event_code
                else:
                    event_code = self._get_event_code(event)
                    if (event_code >= 0): 
                        # button has been pressed:
                        #print("button pressed", event_code)
                        self._inputp(event_code)
                        #print("Last_event", last_event_code)
                        self._cli.send_application_event(self._destination, "REMOTE_IO_SERVICE","KEY_PRESSED",[event_code])
                    
            if last_event_code != invalid_event_code: 
                if event is sg.TIMEOUT_KEY:
                    # button has been released:
                    #print("Time out: Last_event", last_event_code)
                    self._inputr(last_event_code) 
                    self._cli.send_application_event(self._destination,"REMOTE_IO_SERVICE","KEY_RELEASED",[event_code])
                    #event_list.extend([last_event_code,button_release_code])
                    event_code = invalid_event_code
                
                else:
                    event_code = self._get_event_code(event)
                    if (event_code != last_event_code) & (event_code >= 0):
                        # additional button has been pressed:
                    
                        # first release previously pressed button:
                        self._inputr(last_event_code)  
                        self._cli.send_application_event(self._destination,"REMOTE_IO_SERVICE","KEY_RELEASED", [event_code])
                        #event_list.extend([last_event_code,button_release_code])
        
                        # then add new button press event:
                        self._inputp(event_code)  
                        #event_list.extend([event_code,button_release_code])
                        self._cli.send_application_event(self._destination,"REMOTE_IO_SERVICE","KEY_PRESSED", [event_code])
            last_event_code = event_code
         
            if counter > 1000:
                self._cli.alive()
                counter = 0
 
            counter += 1

            self._get_remote_status_update()        

            
    def quit(self):
        self._window.Close()
        os.system('xset r rate 500 33')
        #goodbye()
    
    #while True:
    #    event, values = window.Read()
    #    if event is None:
    #        break
    #    if event is 'Blue':
    #        window.FindElement('canvas').TKCanvas.itemconfig(cir, fill = "Blue")
    #    elif event is 'Red':
    #        window.FindElement('canvas').TKCanvas.itemconfig(cir, fill = "Red")

