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
            for i in self.parralelGPIO:
                GPIO.setup(i, GPIO.OUT)
                GPIO.output(i, GPIO.LOW)


        # CHECK PROTOCOL CSV
        while self.isRunning():

            # PROTOCOL FOUND -> CONTINUE
            if self.playframe_path and os.path.exists(self.playframe_path):
                time.sleep(2.0)
                continue

            try:
                # RE-INIT
                self.stop()

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
                time.sleep(1.0)
        

        # CLOSE
        self.stop()
        self.emit('done')


    def playing(self):
        return self.sound_trig_Thread.playing() if self.sound_trig_Thread else False


    def play(self):
        if self.isRunning() and not self.playing():
            self.sound_trig_Thread = sound_trig_Thread(self)
            self.sound_trig_Thread.start()


    def pause(self):
        if self.sound_trig_Thread:
            self.sound_trig_Thread._paused = True
            self.emit('paused')
            

    def resume(self):
        if self.sound_trig_Thread:
            self.sound_trig_Thread._paused = False
            self.emit('resumed')


    def stop(self):
        if self.sound_trig_Thread:
            self.sound_trig_Thread.stop()
            self.emit('stopped')
            self.sound_trig_Thread.join()
            self.sound_trig_Thread = None
        



# Audio Trig thread
#
class sound_trig_Thread(Thread):

    def __init__(self, core):
        Thread.__init__(self)
        self._playing = False
        self._paused = False
        
        self.lock = Lock()
        self.current = 0
        self.core = core

    def get_GPIO_bool(self, trig_value):
        GPIO_trigOn = [a*b for a,b in zip(self.core.parralelGPIO, bitfield(trig_value))]
        GPIO_trigOn = [g for g in GPIO_trigOn if g > 0]
        # print(bitfield(trig_value), GPIO_trigOn)
        return GPIO_trigOn

    def playing(self):
        return self._playing

    def paused(self):
        return self._paused and self._playing
    
    def stop(self):
        self._playing = False
        self.stream.close()


    # Accurate wait for target time (using time.sleep + busy loop for last millisecond)
    #
    def wait(self, targetDate, txt=''):
        while True:
            delta = (targetDate - datetime.datetime.now()).total_seconds() * 1000
            if delta <= 0.05:
                return True
            time.sleep( 0.1*(delta > 110) + 0.002*(delta > 3) )
            if not self.playing():
                return False
            


    # thread Run
    #
    def run(self):
        
        self.stream = sd.OutputStream(  device = 0, # HifiBerry device
                                        samplerate = 44100, 
                                        channels=2, 
                                        dtype=self.core.sound_dtype
                                        )
        
        self._playing = True
        self._paused = False
        
        if is_RPI():
            GPIO.output(self.core.parralelGPIO, GPIO.LOW)

        nb_items = self.core.playframe.shape[0]
        
        self.core.emit('playing')
        
        startTime = datetime.datetime.now()
        endTime = datetime.datetime.now()
        
        for index, row in self.core.playframe.iterrows():
            
            # Progress
            self.core.emit('progress', int(index*100/nb_items) )
            
            # next Trigger
            GPIO_trigOn = self.get_GPIO_bool(row['Trigger'])     
            
            # next Sample
            stimpath = os.path.join(self.core.stim_path, row['Stimulus'] + '.wav')       
            sound_data, sample_rate = sf.read(stimpath)
            sound_data = sound_data.astype(self.core.sound_dtype)
            audio_duration = sound_data.shape[0] / sample_rate
            
            # pad with silence
            # padd_end = np.zeros(( round(sample_rate * 0.01) , sound_data.shape[1]), dtype=self.core.sound_dtype) 
            # sound_data = np.concatenate((sound_data, padd_end), axis=0) 
            
            # next ISI
            isi_duration = round(row['ISI'] * 10**-3, 3) 
            
            # ----
            
            # let previous ISI terminate
            self.wait(endTime, 'end')
            # print('End: ellpased', (datetime.datetime.now() - startTime).total_seconds() * 1000)
            
            # Check accuracy
            lastEffectiveDuration = (datetime.datetime.now() - startTime).total_seconds() * 1000
            lastWantedDuration = (endTime-startTime).total_seconds() * 1000
            print('Cycle Accuracy: ')
            print('\tLast cycle duration (real/target): ', round(lastEffectiveDuration, 2), '/', round(lastWantedDuration,2))
            print('\tError:', round(lastEffectiveDuration-lastWantedDuration, 2) )
            
            # Pause 
            if self.paused():
                self.core.emit('paused-at', index)
                while self.paused():
                    time.sleep(.1)
                    
            # check Stop
            if not self.playing(): 
                break  
            
            # ----
            
            # Start next sample timing
            startTime = datetime.datetime.now()
            audioTime = startTime + datetime.timedelta(milliseconds= audio_duration*1000)
            endTime = audioTime + datetime.timedelta(milliseconds= isi_duration*1000)
            
            self.core.emit('playing-at', row['Stimulus'], index)
            
            # Play Sample
            try:
                # Start Stream
                self.stream.start()
                
                # Trigger GPIO
                if is_RPI():
                    GPIO.output(GPIO_trigOn,1)
                    
                # Play audio
                self.stream.write(sound_data)

                # Wait for audio duration : stream.write() might return before audio buffer is completely flushed
                self.wait(audioTime, 'audio')
                # print('Audio: ellpased', (datetime.datetime.now() - startTime).total_seconds() * 1000)
                
                # UnTrigger GPIO
                if is_RPI():
                    GPIO.output(GPIO_trigOn, 0)
                    
                # Stop stream (with 20ms safety)
                if isi_duration > 0.02:
                    time.sleep(0.02)
                self.stream.stop()
                
                
            except sd.PortAudioError:
                if self._playing:
                    self.core.emit('error', '- PortAudio -', sd.PortAudioError)
                    self._playing = False
                break
            
            except :
                self._playing = False
                break
            
            
        # Still playing: let last sample/isi terminate
        if self.playing():
            self.core.emit('progress', 100 )
            self.wait(endTime, 'end')
         
        # Was interrupted   
        else:
            self.current = index
            self.core.emit('stopped-at', index)
        
        # End    
        self.stream.close()
        if is_RPI():
            GPIO.output(self.core.parralelGPIO, GPIO.LOW)
        self._playing = False
        self._paused = False
        self.core.emit('done')
        
        
