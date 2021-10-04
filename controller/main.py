import time
import signal
import os, sys, threading
from subprocess import call
from core import CoreInterface
from usbserial import SerialInterface
from config import ConfigInterface

# STATE record
# { 0:BOOT, 1:HELLO, 2:STOP, 3:PLAY, 4:PAUSE, 5:EXIT, 6:OFF, 7:ERROR};


# EXIT handler
#
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum=0, frame=0):
        self.kill_now = True
      


if __name__ == '__main__':
    
    print("\n.:: Stimbox Controller ::.\n")
    
    # EXIT handler
    killer = GracefulKiller()

    # LOCAL storage 
    if not os.path.exists('/data/stimbox'):
        os.makedirs('/data/stimbox')

    # CONFIG
    config = ConfigInterface('/data/stimbox/config.json')

    # SERIAL port to connect M5screen
    serial = SerialInterface("ttyUSB")

    # CORE protocol
    protocol = CoreInterface('/data/usb/', 'playframe.csv', 'stims/')

    #
    # SERIAL events binding
    #

    @serial.on('connected')
    def con(ev, *args):
        time.sleep(0.5)
        protocol.start()

    @serial.on('volup')
    def volup(ev, *args):
        v = config.get("volume")+1
        if v > 100: v = 100
        config.set("volume", v)
        call( ("amixer sset 'Digital' "+str(v)+"%").split(" ") )
        serial.sendVolume(v)

    @serial.on('voldown')
    def volup(ev, *args):
        v = config.get("volume")-1
        if v < 0: v = 0
        config.set("volume", v)
        call( ("amixer sset 'Digital' "+str(v)+"%").split(" ") )
        serial.sendVolume(v)

    @serial.on('play')
    def play(ev, *args):
        protocol.playbackStart()

    @serial.on('resume')
    def play(ev, *args):
        protocol.playbackResume()

    @serial.on('pause')
    def play(ev, *args):
        protocol.playbackPause()

    @serial.on('stop')
    def play(ev, *args):
        protocol.playbackStop()


    #
    # PROTOCOL events binding
    #

    @protocol.on('loading')
    def fn(ev, *args):
        if len(args) > 0:
            serial.sendProtocol(args[0])
        serial.sendState(1)
    
    @protocol.on('ready')
    def fn(ev, *args):
        serial.sendState(2)
        serial.sendVolume(config.get("volume"))

    @protocol.on('playing')
    def fn(ev, *args):
        serial.sendState(3)

    @protocol.on('playing-at')
    def fn(ev, *args):
        serial.sendMedia(args[0])

    @protocol.on('paused')
    def fn(ev, *args):
        serial.sendState(4)

    @protocol.on('resumed')
    def fn(ev, *args):
        serial.sendState(3)

    @protocol.on('stopped')
    def fn(ev, *args):
        serial.sendState(2)    

    @protocol.on('progress')
    def fn(ev, *args):
        serial.sendProgress(args[0])    

    @protocol.on('error')
    def fn(ev, *args):
        serial.sendError(args[0])

    @protocol.on('quit')
    def fn(ev, *args):
        killer.exit_gracefully()

    # CATCH ERRORS
    def excepthook(*args):
        if len(args) > 0:
            error = "- "+str(args[0].exc_type)+" -:"+str(args[0].exc_value)
        else:
            error = "- Fatal Error -: :sorry..."
        protocol.emit('error', error)
    threading.excepthook = excepthook


    # START
    serial.start()
    
    # WAIT until close
    while not killer.kill_now:
        time.sleep(0.2)


    # CLOSE
    serial.sendState(5)
    config.flush()
    time.sleep(0.5)
    serial.sendState(6)

    serial.quit()
    protocol.quit()
    
    print("\nGoodbye :)")
