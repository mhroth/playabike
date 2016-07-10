# Copyright 2016 Martin Roth (mhroth@gmail.com). All Rights Reserved.

import os
import random
import sys
import time

sys.path.append(os.path.abspath("../BiblioPixel"))
from bibliopixel.led import *
from bibliopixel.animation import *
from bibliopixel.drivers.serial_driver import *
from bibliopixel.drivers.visualizer import *
from bibliopixel.gamma import *

def rgb2mA(rgb, gamma=None):
    """ Returns the number of milliamps used during this step
        for a given RGB tuple. Accounts for the given gamma correction.
    """
    if gamma:
        rgb = (gamma[x] for x in rgb)

    # assume 50mA at full brightness
    return (50.0/(255.0*3.0)) * sum(rgb)

# class StripTest(BaseStripAnim):
#     def __init__(self, led, fps=None, gamma=None, start=0, end=-1):
#         #The base class MUST be initialized by calling super like this
#         super(StripTest, self).__init__(led, start, end)
#         #Create a color array to use in the animation
#         self._colors = [colors.Red, colors.Orange, colors.Yellow, colors.Green, colors.Blue, colors.Indigo]
#
#         if fps:
#             self._internalDelay = int(1000.0/fps)
#
#         self.__total_Ah = 0.0
#         self.__gamma = gamma
#
#     def preRun(self, amt=1):
#         self._led.all_off()
#         self.__start_time = self._msTime()
#
#     def step(self, amt=1):
#         # Fill the strip, with each sucessive color
#         total_mA = 0.0
#         for i in range(self._led.numLEDs):
#             rgb = self._colors[(self._step + i) % len(self._colors)]
#             self._led.set(i, rgb)
#             total_mA += rgb2mA(rgb, self.__gamma)
#         self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
#         print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))
#
#         # Increment the internal step by the given amount
#         self._step += amt

class Rule90Anim(BaseStripAnim):
    def __init__(self, led, fps=None, gamma=None, start=0, end=-1):
        #The base class MUST be initialized by calling super like this
        super(Rule90Anim, self).__init__(led, start, end)
        #Create a color array to use in the animation
        self._colors = [colors.Red, colors.Orange, colors.Yellow, colors.Green, colors.Blue, colors.Indigo]

        if fps:
            self._internalDelay = int(1000.0/fps)

        self.__total_Ah = 0.0
        self.__gamma = gamma

        # start with random state
        self.__currentState = 0
        self.__ca_state = [
            [0 for _ in range(led.numLEDs+2)],
            [0 for _ in range(led.numLEDs+2)]
        ]
        self.__ca_state[self.__currentState][int(led.numLEDs/2)] = 1 # for Sirpenski Triangle

        # Rule 90
        self.__ca_rules = {
            (0,0,0): 0,
            (0,0,1): 1,
            (0,1,0): 0,
            (0,1,1): 1,
            (1,0,0): 1,
            (1,0,1): 0,
            (1,1,0): 1,
            (1,1,1): 0
        }

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        # Fill the strip, with each sucessive color
        total_mA = 0.0

        # update CA state
        curent_state = self.__ca_state[self.__currentState]
        new_state = self.__ca_state[self.__currentState^1]
        for i in range(1,led.numLEDs+1):
            new_state[i] = self.__ca_rules[tuple(curent_state[i-1:i+2])]
        new_state[0] = new_state[led.numLEDs]
        new_state[led.numLEDs+1] = new_state[1]
        self.__currentState ^= 1 # switch state

        # update LED values
        for i in range(self._led.numLEDs):
            rgb = (0,0,0) if new_state[i+1] == 0 else (255,255,255)
            self._led.set(i, rgb)
            total_mA += rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))

        # Increment the internal step by the given amount
        self._step += amt

#create driver for a 30 pixels
# https://github.com/ManiacalLabs/BiblioPixel/wiki/DriverSerial
# driver = DriverSerial(LEDTYPE.APA102, 5*30, SPISpeed=24, gamma=gamma.APA102)
driver = DriverVisualizer(5*30)

# https://github.com/ManiacalLabs/BiblioPixel/wiki/LEDStrip
led = LEDStrip(driver)

anim = Rule90Anim(led, fps=10, gamma=gamma.APA102)
anim.run()

# writing an animation
# https://github.com/ManiacalLabs/BiblioPixel/wiki/Writing-an-Animation
