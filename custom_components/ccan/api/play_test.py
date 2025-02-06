


import time
import sys
import subprocess
import os.path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QKeyEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QFrame, QSlider, QHBoxLayout, QPushButton, \
    QVBoxLayout, QAction, QFileDialog, QApplication
from PyQt5.QtGui import QFont
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel
import vlc
import sys
import socket
import MySocket
import struct


class Player(QMainWindow):
    """A simple Media Player using VLC and Qt
    """
    def __init__(self, master=None):
        QMainWindow.__init__(self, master)
        QMainWindow.showMaximized(self)
        self.setWindowTitle("Media Player")
        #self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)

        self._t1 = 0
        self._t2 = 0

        # creating a basic vlc instance
        self.instance = vlc.Instance('--no-audio')
        # creating an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()


        #m = self.instance.media_new("axrtpm://guest:guest@192.168.2.7/axis-media/media.amp")
        #axrtpm://<ip>/axis-media/media.amp
        
        #self.mediaplayer.set_media(m)
        #self.mediaplayer.play()

    
        self.counter = 0
        
        self._display_on_command  = "xrandr --output VGA-2 --brightness 1.0"
        self._display_off_command = "xrandr --output VGA-2 --brightness 0.5"
        self._monitor_wakeup      = "DISPLAY=:0 xset dpms force on"
        self._monitor_fall_asleep = "DISPLAY=:0 xset dpms force off"        

        self._sleep = False        
        
        self._timer_start = 0
        self._timer_black = 0
        self._timer_asleep = 0
        self.__awake_default = 20
        self.__wakeup_time   =  10
       
        self._bus_received = 0
        # only 69s with no received messages:
        self._bus_timeout  = 60
               
        self.createUI()
        self._reconnect() 
        #self._window_id = subprocess.Popen('xwininfo -root | grep xwininfo | cut -d" " -f4', stdout=subprocess.PIPE, shell=True).stdout.read().strip()

    def mousePressEvent(self,event):
        event.accept()
        self.Start()

    def keyPressEvent(self, event):
        #if type(event) == QKeyEvent:
        #self.label.setText('Key pressed..')
        event.accept()
        #else:
        #    self.label.setText('Any other event..')
        #    event.ignore()
        self.Start()
        
    def eventFilter(self, source, event):
        pass
        #self.label.setText('Mouse moved..')
        #event.accept()
        #else:
        #    self.label.setText('Any other event..')
        #    event.ignore()
        #self.Start()

    def createUI(self):
        """Set up the user interface, signals & slots
        """
        test = 1
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

  
        self.videoframe = QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QPalette.Window,
                               QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)


        self.vboxlayout = QVBoxLayout()
        self.widget.setLayout(self.vboxlayout)

        self.label = QLabel("Außentemperatur:")
        self.label.setFont(QFont('SansSerif', 20))  
        #self.label.setGeometry(QtCore.QRect(20, 20, 80, 30)) #(x, y, width, height)
        self.label.setFixedHeight(30)

        self.vboxlayout.addWidget(self.label)
        self.vboxlayout.addWidget(self.videoframe)

        open = QAction("&Open", self)
   
        # Check every 1/100s for new messages
        
        self.timerMessages = QTimer(self)
        self.timerMessages.timeout.connect(self.ReceiveMessages)
        self.timerMessages.start(10)
   
        self.timerPlay = QTimer(self)
        #self.timerPlay.setSingleShot(True) 
        self.timerPlay.timeout.connect(self.Count)    
        self.timerPlay.start(1000)

        self.__count = 0
        self.__awake_time = self.__awake_default


    def Count(self):
        
        self._bus_received += 1

        if self._bus_received > self._bus_timeout:
            self._reconnect()
        
        if self._sleep == True:
            return
        
        self.__count += 1
        
        if self.__count > self.__awake_time + 10:
            self.mediaplayer.stop()
            os.system(self._monitor_fall_asleep)
            self._sleep = True
        
        if self.__count > self.__awake_time:
            os.system(self._display_off_command)
     

    def _reconnect(self):
        self.client = MySocket.MySocket()
        self.client.connect("192.168.2.100", 3600)
        text = "Außentemperatur: <unbekannt>"
        self.label.setText(text)
        
   
    def ReceiveMessages(self):    
        msg = self.client.myreceive()
        if msg is None:
            return
        
        self._bus_received = 0
        
        source = struct.unpack('iicccccccc',msg)
      
        if source[1] == 5 and ord(source[2]) == 5:
            # check whether the message is a temp info from sensor 100:
            if ord(source[3]) == 34 and ord(source[4]) == 100:
                # calc temperature
                temp = ord(source[5])*256 + ord(source[6])
                text = "Außentemperatur: {0:2.1f}°C"
                self.label.setText(text.format(temp/16))
  
    
        if source[1] == 3 and ord(source[3]) == 10 and ord(source[4]) == 87:
                    # check whether the message is a temp info from powerport group 87 (Klingel)
                    #if ord(source[3]) == 10 and ord(source[4]) == 87:
                    #self.label.setText('Klingel betätigt')
            self.Start()
    
    
                # ID = 52 : Melder vor dem kleinen fenster / ARbeitszimmer
                # 
                #if source[1] == 3 and ord(source[3]) == 76 and ord(source[4]) == 52:
                #    # check whether the message is a temp info from powerport group 87 (Klingel)
                #    #if ord(source[3]) == 10 and ord(source[4]) == 80:
                #    #self.label.setText('Bewegungsmelder Arbeitszimmer ')
                #    self.Start()
    
        if source[1] == 3 and ord(source[3]) == 76 and ord(source[4]) == 80:
                    # check whether the message is a temp info from motion sensor (main door)
                    #if ord(source[3]) == 10 and ord(source[4]) == 80:
                    #self.label.setText('Bewegungsmelder Eingangstür')
            self.Start()

    def Start(self):
        #print("RESTARTED..")
        self.__count = 0
        #self.timerPlay.stop()
                   
        if self._sleep is True:
            self._sleep = False
            os.system(self._monitor_wakeup)
            os.system(self._display_on_command)
            self.mediaplayer.play()
            self.__awake_time = self.__awake_default + self.__wake_time_time
  
        else:
            os.system(self._display_on_command)
            self.__awake_time = self.__awake_default
 
        self._sleep = False
   
    def Stop(self):
        print("MONITOR BLACK")
        quit()
        self._sleep = False
        #self.mediaplayer.stop()
        #self.timerPlay.singleShot(10000, self.Start)
        os.system(self._display_off_command)
     
        self.timerPlay.timeout.connect(self.fall_asleep)    
        self.timerPlay.start(20000)
        #self.timerPlay.singleShot(20000, self.fall_asleep)
        self._timer_black = time.time()
        print(str(self._timer_black-self._timer_start)+"s elapsed since start")
                     
    def fall_asleep(self):
        quit()
        print("ASLEEP..")
        self._timer_asleep = time.time()
        self._sleep = True
        self.mediaplayer.stop()
        os.system(self._monitor_fall_asleep)
        print(str(self._timer_black-self._timer_start)+"s elapsed since monitor made black")
    
    
    
    def wake_up(self):
        quit()


    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        
        self.media = self.instance.media_new("rtsp://guest:guest@192.168.2.7/axis-media/media.amp")
        # put the media in the media player

        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))

        self.mediaplayer.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player()
    player.show()
    #player.resize(640, 480)
 
    #time.sleep(1)
    
    #player.OpenFile("rtsp://guest:guest@192.168.2.7/axis-media/media.amp")
    player.OpenFile()
    #player.OpenFile();
    sys.exit(app.exec_())
	
