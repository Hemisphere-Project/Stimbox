import time
import signal
from usbserial import SerialInterface


state = 0       # { 0:BOOT, 1:HELLO, 2:STOP, 3:PLAY, 4:PAUSE, 5:EXIT, 6:OFF};
volume = 80

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True


if __name__ == '__main__':
    
    print("\n.:: Stimbox Controller ::.\n")
    killer = GracefulKiller()

    serial = SerialInterface(None, "ttyUSB")
    
    @serial.on('connected')
    def con(ev, *args):
        time.sleep(1)
        state = 2
        serial.sendState(state)
        serial.sendVolume(volume)

    @serial.on('volup')
    def volup(ev, *args):
        global volume
        volume += 1
        serial.sendVolume(volume)

    @serial.on('voldown')
    def volup(ev, *args):
        global volume
        volume -= 1
        serial.sendVolume(volume)

    @serial.on('play')
    @serial.on('resume')
    def play(ev, *args):
        state = 3
        serial.sendState(state)
        serial.sendMedia("super_genial_0.wav")

    @serial.on('pause')
    def play(ev, *args):
        state = 4
        serial.sendState(state)

    @serial.on('stop')
    def play(ev, *args):
        state = 2
        serial.sendState(state)


    serial.start()

    while not killer.kill_now:
        time.sleep(0.2)

    state = 5
    serial.sendState(state)

    # Clean close
    time.sleep(1)
    #

    state = 6
    serial.sendState(state)

    serial.quit()
    
    print("\nGoodbye :)")
