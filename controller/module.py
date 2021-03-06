import threading
from abc import ABC, abstractmethod
from pymitter import EventEmitter
from termcolor import colored
import sys, threading


def safe_print(*args, sep=" ", end="", **kwargs):
    joined_string = sep.join([ str(arg) for arg in args ])
    print(joined_string  + "\n", sep=sep, end=end, **kwargs)


class EventEmitterX(EventEmitter):
    def emit(self, event, *args):
        # prepend event to args
        a = [event] + list(args)
        super().emit(event, *a)


class Module(EventEmitterX):
    def __init__(self, parent, name, color):
        super().__init__(wildcard=True, delimiter=".")
        self.name = name.replace(" ", "_")
        self.nameP = colored(('['+self.name+']').ljust(10, ' ')+' ', color)
        self.parent = parent
        self.logEvents = True

    def log(self, *argv):
        safe_print(self.nameP, *argv)
        sys.stdout.flush()

    # Emit extended
    def emit(self, event, *args):
        fullEvent = self.name.lower() + '.' + event
        if self.logEvents:
            self.log('-', event, *args )

        super().emit(event, *args) 
        if (self.parent):
            self.parent.emit(fullEvent, *args)


class BaseInterface(ABC, Module):

    def  __init__(self, parent, name="INTERFACE", color="blue"):
        super().__init__(parent, name, color)

        # stopping flag
        self.stopped = threading.Event()
        self.stopped.set()

        # Listen thread
        self.recvThread = threading.Thread(target=self.listen)


    # Receiver THREAD (ABSTRACT)
    @abstractmethod
    def listen(self):
        self.stopped.wait()

    # Start
    def start(self):
        self.stopped.clear()
        self.recvThread.start()
        return self

    # Stop
    def quit(self):
        self.log("stopping...")
        self.stopped.set()
        self.recvThread.join()
        self.log("stopped")

	# is Running
    def isRunning(self, state=None):
        if state is not None:
            self.stopped.clear() if state else self.stopped.set()
        return not self.stopped.is_set()



        