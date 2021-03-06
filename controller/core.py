# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import os
import soundfile as sf
import sounddevice as sd
import time

import io
def is_RPI():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

if is_RPI():
    import RPi.GPIO as GPIO

# import numpy as np
import pandas as pd
from threading import Thread, Lock

from module import BaseInterface
'''
This code is the one used on the Raspberry Pi box (no gui)
'''  

def bitfield(n):
    return [n >> i & 1 for i in range(7,-1,-1)]


# CORE interface
#
class CoreInterface (BaseInterface):

    parralelGPIO = [16,15,18,19,22,21,24,23]

    # CORE init
    def  __init__(self):
        super(CoreInterface, self).__init__(None, "Core")
        self._playing = False
        self._paused = False
        self.sound_trig_Thread = None
        self.playframe = pd.read_csv('/data/usb/playframe.csv')
        self.stim_folder = '/data/usb/stims/'
        self.sound_dtype = 'float32'
        self.emit('init')


    # CORE thread
    def listen(self):
        if is_RPI():
            GPIO.setmode(GPIO.BOARD)
        self.stream = sd.OutputStream(  device = 0, # HifiBerry device
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
                self._paused = False
                self.emit('playing')


    def playbackPause(self):
        self._paused = True
        self.emit('paused')

    def playbackResume(self):
        self._paused = False
        self.emit('resumed')


    def playbackStop(self):
        if self.sound_trig_Thread:
            self.sound_trig_Thread.stop()


    def playbackEnd(self):
        self.stream.abort()
        self._playing = False
        self._paused = False
        self.emit('stopped')


# Audio Trig thread
#
class sound_trig_Thread(Thread):
    def __init__(self, core):
        Thread.__init__(self)
        self.lock = Lock()
        self._running = False
        self.current = 0
        self.core = core

        if is_RPI():
            for i in self.core.parralelGPIO:
                GPIO.setup(i, GPIO.OUT)
                GPIO.output(i, GPIO.LOW)

    def get_GPIO_bool(self, trig_value):
        GPIO_trigOn = [a*b for a,b in zip(self.core.parralelGPIO, bitfield(trig_value))]
        GPIO_trigOn = [g for g in GPIO_trigOn if g > 0]
        # print(bitfield(trig_value), GPIO_trigOn)
        return GPIO_trigOn

    def running(self):
        with self.lock:
            return self._running


    def run(self):
        with self.lock:
            self._running = True

        nb_items = self.core.playframe.shape[0]
        
        for index, row in self.core.playframe.iterrows():   #playframe.iloc[self.current:]
            
            if self.core._paused:
                self.core.emit('paused-at', index)

            while self.core._paused and self.running():
                time.sleep(.1)

            if not self.running():
                self.current = index
                self.core.emit('stopped-at', index)
                break
            
            self.core.emit('progress', int(index*100/nb_items) )
            
            # self.core.log('Reading', row['Stimulus'], 'at index', index)

            sound_data, sample_rate = sf.read(self.core.stim_folder + row['Stimulus'] + '.wav')
            sound_data = sound_data.astype(self.core.sound_dtype)
            GPIO_trigOn = self.get_GPIO_bool(row['Trigger'])
            isi = round(row['ISI'] * 10**-3, 3)

            try:
                self.core.stream.start()
                if is_RPI():
                    GPIO.output(GPIO_trigOn,1)
                self.core.emit('playing-at', row['Stimulus'], index)
                self.core.stream.write(sound_data)
                self.core.stream.stop()
            except sd.PortAudioError:
                self.core.log('PortAudio ERROR:', sd.PortAudioError)
                return
            except :
                return

            if is_RPI():
                GPIO.output(GPIO_trigOn, 0)
            self.core.log('isi:', isi)
            time.sleep(isi)

        if self.running():
            self.core.emit('progress', 100 )

        self.core.playbackEnd()

        
        

    def stop(self):
        with self.lock:
            self._running = False

    
