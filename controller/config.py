from module import BaseInterface
import os
import json
from threading import Timer


class ConfigInterface (BaseInterface):
    
    values = {
        "volume": 80
    }

    def __init__(self, path='/tmp/stimbox.json'):
        super(ConfigInterface, self).__init__(None, "Config", "green")

        self.dirtyTimer = None
        self._path = path
        
        if os.path.isfile(self._path):
            config = {}
            with open(self._path, 'r') as f:
                config = json.load(f)
            self.values = {**self.values, **config}
            self.log("loaded", self.values)
            


    def save(self):
        with open(self._path, 'w') as f:
            json.dump(self.values, f)
        self.log("saved", self.values)


    def get(self, key):
        return self.values[key]


    def set(self, key, value):
        self.values[key] = value
        self.flush()


    def flush(self, forceNow = False):
        if self.dirtyTimer:
            self.dirtyTimer.cancel()
        if forceNow:
            self.save()
        else:
            self.dirtyTimer = Timer(5.0, self.save)
            self.dirtyTimer.start()

    def listen(self):
        self.stopped.wait()