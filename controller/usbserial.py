from module import BaseInterface

import time
import serial
from serial.tools import list_ports


class SerialInterface (BaseInterface):

    def  __init__(self, parent, filter="", maxRetry=0):
        super(SerialInterface, self).__init__(parent, "Serial")
        self.port = None
        self.serial = None
        self.filter = filter
        self.maxRetry = maxRetry
        
        self._hardClear = True


    # SERIAL receiver THREAD
    def listen(self):

        retryCount = 0
        while self.isRunning():

            # find port
            if not self.port:
                retryCount += 1 
                if self.maxRetry == 0 or retryCount <= self.maxRetry:
                    for dev in list_ports.grep(self.filter):
                        self.port = dev.device
                        break
                    if self.port: continue
                    self.log("no device found.. retrying")
                for i in range(10):
                    time.sleep(0.5)
                    if not self.isRunning(): 
                        return
            
            # connect to serial
            elif not self.serial:
                try:
                    # Reset 
                    self.serial = serial.Serial(self.port) # dummy connection to receive all the watchdog gibberish (unplug + replug) and properly reset the arduino
                    with self.serial:
                        self.serial.setDTR(False)   # reset flag
                        time.sleep(1)
                        self.serial.flushInput()
                        self.serial.setDTR(True)
                        time.sleep(0.5)
                    
                    # Connect
                    self.serial = serial.Serial(self.port, 115200, timeout=.1)
                    self.log("connected to", self.port, "!")
                    self.clear()
                    
                except:
                    self.log("connection failed on", self.port)
                    self.port = None
                    self.serial = None
                    time.sleep(0.5)
                    

            # read / write
            else:
                try:

                    # READ
                    data = self.serial.readline()[:-2] #the last bit gets rid of the new-line chars
                    if data: 
                        data = data.decode("utf-8").split(' ')
                        data[0] = data[0].lower()
                        if data[0][0] == '/': data[0] = data[0][1:]
                        data[0].replace('/','.')
                        self.emit(data[0], *data[1:])

                    # REFRESH
                    else:
                        self.refresh()
                        time.sleep(0.1)

                    # # CLEAR
                    # if self._hardClear: 
                    #     self.serial.write( ('¤0').encode() )
                    #     self._hardClear = False

                    # # WRITE
                    # say = None
                    # for i,l in enumerate(self._buffer):
                    #     if l['dirty']:
                    #         if not say: say = '¤'
                    #         else: say += '£'
                    #         say += str(i+1)
                    #         say += l['txt'].ljust(26, ' ')
                    #         l['dirty'] = False
                    
                    # if say:
                    #     # self.log(say.encode())
                    #     self.serial.write( say.encode() )
                    #     # self.log(say)


                except Exception as e:
                    print(e)
                    self.log("broken link..")
                    self.serial = None
                    time.sleep(0.5)

    
    def clear(self):
        self._hardClear = True

    
    def refresh(self):
        pass