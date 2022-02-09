# -*- coding: utf-8 -*-
# Copyright (c) 2016, French National Center for Scientific Research (CNRS)
# Distributed under the (new) BSD License. See LICENSE for more info.

import os
import soundfile as sf
import sounddevice as sd
import time
import datetime
import re

import io
def is_RPI():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

if is_RPI():
    import RPi.GPIO as GPIO

import numpy as np
import pandas as pd
from threading import Thread, Lock

from module import BaseInterface
'''
This code is the one used on the Raspberry Pi box (no gui)
'''  

def bitfield(n):
    return [n >> i & 1 for i in range(7,-1,-1)]


class UsbDriveError(Exception):
    pass


# CORE interface
#
class CoreInterface (BaseInterface):

    parralelGPIO = [16,15,18,19,22,21,24,23]

    # CORE init
    def  __init__(self, basePath, protoCsv, stimsPath):
        super(CoreInterface, self).__init__(None, "Core")
        self._playing = False
        self._paused = False
        self.sound_trig_Thread = None

        self.base_path = basePath
        self.playframe_file = protoCsv
        self.playframe_path = None
        self.stim_folder = stimsPath
        self.stim_path = None

        self.sound_dtype = 'float32'
        self.emit('init')


    # CORE thread
    def listen(self):
        if is_RPI():
            GPIO.setmode(GPIO.BOARD)
        self.stream = sd.OutputStream(  device = 0, # HifiBerry device
                                        samplerate = 44100, 
                                        channels=2, 
                                        dtype=self.sound_dtype
                                        )

        # List directories
        # protoFolders = [ p for p in next(os.walk(self.base_path))[1] if os.path.exists(os.path.join(p, self.playframe_file))]
        # print(protoFolders)

        # CHECK PROTOCOL CSV
        while self.isRunning():

            # PROTOCOL FOUND -> CONTINUE
            if self.playframe_path and os.path.exists(self.playframe_path):
                time.sleep(2.0)
                continue

            try:
                # RE-INIT
                self.playbackEnd()

                # RESET PATH
                self.playframe_path = None
                self.stim_path = None

                # SEARCH PROTOCOL
                protoFolders = [ p for p in os.listdir(self.base_path) if os.path.exists(os.path.join(self.base_path, p, self.playframe_file)) ]
                if len(protoFolders) == 0:
                    raise UsbDriveError("Can't find folder:containing '"+self.playframe_file+"'")
                elif len(protoFolders) > 1:
                    raise UsbDriveError("Multiple protocol found.:only one protocol allowed per key !")
                
                # LOAD PROTOCOL
                self.playframe_path = os.path.join(self.base_path, protoFolders[0], self.playframe_file)
                self.playframe = pd.read_csv(self.playframe_path)
                self.emit("loading", protoFolders[0])

                # CHECK STIMS PATH
                self.stim_path = os.path.join(self.base_path, protoFolders[0], self.stim_folder)
                if not os.path.exists(self.stim_path):
                    raise UsbDriveError(os.path.join(protoFolders[0], self.stim_folder)+":folder not found..")
                
                # CHECK ALL STIM FILES
                stimfiles = list(set([row['Stimulus'] for index, row in self.playframe.iterrows()]))
                for f in stimfiles:
                    stim = os.path.join(protoFolders[0], self.stim_folder, f + '.wav')
                    if not os.path.exists(os.path.join(self.base_path,stim)):
                        raise UsbDriveError("file missing in stims folder:"+f + '.wav')
                
                self.emit('ready', protoFolders[0])

            # EMIT ERROR
            except Exception as e:
                self.playframe_path = None
                error = "- "+type(e).__name__.replace('Error', '')+" -"
                error += ":"+re.sub(r'\[.*\] ', '', str(e))
                self.emit('error', error)
                time.sleep(2.0)
        

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

            stimpath = os.path.join(self.core.stim_path, row['Stimulus'] + '.wav')
            # startTime = datetime.datetime.now()
            
            # Get Duration
            # f = sf.SoundFile(stimpath)
            # theoricalDuration = int(f.frames *1000 / f.samplerate)
            
            # Load file
            sound_data, sample_rate = sf.read(stimpath)
            sound_data = sound_data.astype(self.core.sound_dtype)
            
            # Prepare Trigger / ISI
            GPIO_trigOn = self.get_GPIO_bool(row['Trigger'])
            isi = round(row['ISI'] * 10**-3, 3)
            
            # Add 0 padding to improves sound quality (in case of very short sounds)
            padd_end = np.zeros((round(sample_rate*0.05), sound_data.shape[1]), dtype=self.core.sound_dtype) # add 50ms
            # isi -= 0.0626  # Correspond au -0.5 sur v1 (mais isi 30ms trop court)
            isi -= 0.0626 - 0.03
            sound_data = np.concatenate((sound_data, padd_end), axis=0)  
            
            try:
                self.core.stream.start()
                if is_RPI():
                    GPIO.output(GPIO_trigOn,1)
                self.core.emit('playing-at', row['Stimulus'], index)
                self.core.stream.write(sound_data)
                self.core.stream.stop()
            except sd.PortAudioError:
                self.emit('error', '- PortAudio -', sd.PortAudioError)
                time.sleep(2.0)
                self.playbackEnd()
                return
            except :
                return

            if is_RPI():
                GPIO.output(GPIO_trigOn, 0)

            # effectiveDuration = int((datetime.datetime.now() - startTime).total_seconds() * 1000)
            # print('Duration', effectiveDuration, theoricalDuration)
            # self.core.log('isi theorical:', isi, ' // isi corrected:', isi-(effectiveDuration-theoricalDuration)/1000)
            # time.sleep(isi-(effectiveDuration-theoricalDuration)/1000)

            self.core.log('isi:', isi)
            time.sleep(isi)


        if self.running():
            self.core.emit('progress', 100 )

        self.core.playbackEnd()
        self.core.emit('stopped')

        
        

    def stop(self):
        with self.lock:
            self._running = False

    
