import time
import signal
from usbserial import SerialInterface

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
    serial.start()

    while not killer.kill_now:
        time.sleep(0.5)

    serial.quit()
    
    print("\nGoodbye :)")
