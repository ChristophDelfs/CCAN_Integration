'''
Created on 28.08.2018

@author: christoph
'''

import socket

class MySocket:
    '''demonstration class only
      - coded for clarity, not efficiency
    '''
 

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.sock = sock

        self.MSGLEN = 16
        self.sock.setblocking(0)
          
    def connect(self, host, port):
        self.sock.connect((host, port))
        r = ' '
        self.sock.send(r.encode())

    def mysend(self, msg):
       
    
        sent = self.sock.send(msg)
        if sent == 0:
            raise RuntimeError("socket connection broken")
          

    def myreceive(self):
        #self.mysend('') # keep alive
        try:
            msg = self.sock.recv(self.MSGLEN)
        except:
            msg = None
            
        return msg
    
    
     