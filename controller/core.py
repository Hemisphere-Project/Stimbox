# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import os
import soundfile as sf
import sounddevice as sd
import time

import RPi.GPIO as GPIO
# import numpy as np
import pandas as pd
from threading import Thread, Lock

from module import BaseInterface
'''
This code is the one used on the Raspberry Pi box (no gui)
'''  


# CORE interface
#
class CoreInterface (BaseInterface):

    parralelGPIO = [32,18,36,37,16,33,23,21]

    # CORE init
    def  __init__(self):
        super(CoreInterface, self).__init__(None, "Core")
        self._playing = False
        self.playframe = pd.read_csv('/data/usb/playframe_ex1.csv')
        self.stim_folder = '/data/usb/stims/'
        self.sound_dtype = 'float32'
        self.emit('init')


    # CORE thread
    def listen(self):
        GPIO.setmode(GPIO.BOARD)
        self.stream = sd.OutputStream(  device = 5, # HifiBerry device
                                        samplerate = 44100, 
                                        channels=2, 
                                        dtype=self.sound_dtype)

        # WAIT until program exits
        self.emit('ready')
        self.stopped.wait()

        # CLOSE
        self.playbackStop()
        self.stream.close()
        self.emit('done')


    def playing(self):
        return self._playing #could be a mutex ?


    def playbackStart(self):
        if self.isRunning():
            if not self.playing():
                self.sound_trig_Thread = sound_trig_Thread(self)
                self.sound_trig_Thread.start()
                self._playing = True
                self.emit('playing')


    def playbackPause(self):
        self.emit('paused')
        #TODO
        pass


    def playbackStop(self):
        if self._playing:
            self.sound_trig_Thread.stop()
            self._playing = False
            self.emit('stopped')




# Audio Trig thread
#
class sound_trig_Thread(Thread):
    def __init__(self, core):
        Thread.__init__(self)
        self.lock = Lock()
        self._running = False
        self.current = 0

        for i in self.core.parralelGPIO:
            GPIO.setup(i.item(), GPIO.OUT)
            GPIO.output(i.item(), GPIO.LOW)

    def get_GPIO_bool(self, trig_value):
        list('{0:08b}'.format(trig_value))
        print(list('{0:08b}'.format(trig_value)))
        # bool_filter = np.array(np.array(list('{0:08b}'.format(trig_value))), dtype=bool)
        # GPIO_trigOn = self.core.parralelGPIO[bool_filter].tolist()
        return self.core.parralelGPIO

    def running(self):
        with self.lock:
            return self._running


    def run(self):
        with self.lock:
            self._running = True

        nb_items = self.core.playframe.shape[0]

        for index, row in self.core.playframe.iterrows():   #playframe.iloc[self.current:]
            if not self.running():
                self.current = index
                self.core.emit('stopped-at', index)
                break
            
            self.core.emit('progress', int(index*100/nb_items) )
            
            self.core.log('Reading', row['Stimulus'], 'at index', index)

            sound_data, sample_rate = sf.read(self.core.stim_folder + row['Stimulus'] + '.wav')
            sound_data = sound_data.astype(self.core.sound_dtype)
            GPIO_trigOn = self.get_GPIO_bool(row['Trigger'])
            isi = round(row['ISI'] * 10**-3, 3)

            try:
                self.core.stream.start()
                GPIO.output(GPIO_trigOn,1)
                self.core.emit('playing-at', row['Stimulus'], index)
                self.core.stream.write(sound_data)
                self.core.stream.stop()
            except sd.PortAudioError:
                self.core.log('PortAudio ERROR:', sd.PortAudioError)
                return
            except :
                return

            GPIO.output(GPIO_trigOn, 0)
            self.core.log('isi:', isi)
            time.sleep(isi)

        self.core.emit('end')

    def stop(self):
        with self.lock:
            self._running = False
        self.core.stream.abort()

    
