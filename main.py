# Copyright 2016 Martin Roth (mhroth@gmail.com). All Rights Reserved.

import colorsys
import math
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

from WaveAnim import WaveAnim
from LorenzAnim import LorenzAnim
from CellularAutomataAnim importy CellularAutomataAnim

# TODO(mhroth):
#  gravity, solar systems
#  lorenz attractor (x, y, z) coordinates
#    some chaos system
#  wave equation
#    2 waves with different colors that mix
#    differnet kinds of boundary conditions
#    waves with damping
#  1D cellular automata
#

def rgb2mA(rgb, gamma=None):
    """ Returns the number of milliamps used during this step
        for a given RGB tuple. Accounts for the given gamma correction.
    """
    if gamma:
        rgb = (gamma[x] for x in rgb)

    # assume 50mA at full brightness
    return (50.0/(255.0*3.0)) * sum(rgb)

def tween(start_state, end_state, step, num_iterations=10, tween_state=None):
    assert len(start_state) == len(end_state)
    out = tween_state or list(start_state)
    for i in range(len(start_state)):
        m = (end_state[i]-start_state[i]) / float(num_iterations) # slope
        out[i] = (step%num_iterations)*m + start_state[i]
    return out

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

__FPS = 60

#create driver for a 30 pixels
# https://github.com/ManiacalLabs/BiblioPixel/wiki/DriverSerial
driver = DriverSerial(LEDTYPE.APA102, 30, SPISpeed=24, gamma=gamma.APA102)
# driver = DriverVisualizer(5*30)

# https://github.com/ManiacalLabs/BiblioPixel/wiki/LEDStrip
led = LEDStrip(driver)

# anim = CellularAutomataAnim(led, fps=__FPS, gamma=gamma.APA102, tween_time=4)
# anim = WaveAnim(led, fps=__FPS, gamma=gamma.APA102, mean_impulse_period=30.0)
anim = LorenzAnim(led, fps=__FPS, gamma=gamma.APA102)
anim.run()

# writing an animation
# https://github.com/ManiacalLabs/BiblioPixel/wiki/Writing-an-Animation
