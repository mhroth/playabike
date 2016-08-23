# Copyright 2016 Martin Roth (mhroth@gmail.com). All Rights Reserved.

import math
import os
import random
import sys

sys.path.append(os.path.abspath("../BiblioPixel"))
from bibliopixel.led import *
from bibliopixel.animation import *
from bibliopixel.drivers.serial_driver import *
from bibliopixel.drivers.visualizer import *
from bibliopixel.gamma import *

class GravityAnim(BaseStripAnim):
    def __init__(self, led, fps, gamma=None, start=0, end=-1):
        #The base class MUST be initialized by calling super like this
        super(GravityAnim, self).__init__(led, start, end)

        if fps:
            self._internalDelay = int(1000.0/fps)

        self.__total_Ah = 0.0
        self.__gamma = gamma

        self.__pos = [[0.0,0.0], [1.0,0.0]]
        self.__vel = [[0.0,0.0], [1.0,0.0]]
        self.__mass = [1.0, 1.0]

    def __rgb2mA(self, rgb, gamma=None):
        """ Returns the number of milliamps used during this step
            for a given RGB tuple. Accounts for the given gamma correction.
        """
        if gamma:
            rgb = (gamma[x] for x in rgb)

        # assume 60mA at full brightness
        return (60.0/(255.0*3.0)) * sum(rgb)

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        total_mA = 0.0

        dt = self._internalDelay/1000.0
        r_x = self.__pos[0][0] - self.__pos[1][0]
        r_y = self.__pos[0][1] - self.__pos[1][1]
        r = math.sqrt(r_x**2 + r_y**2)
        f_x = (r_x/r)*(self.__mass[0]*self.__mass[1])/(r**2)
        f_y = (r_y/r)*(self.__mass[0]*self.__mass[1])/(r**2)
        self.__vel[0][0] += -f_x*dt/self.__mass[0] # minus because the force is in the opposite direction
        self.__vel[1][0] += f_x*dt/self.__mass[1]
        self.__vel[0][1] += -f_y*dt/self.__mass[0]
        self.__vel[1][1] += f_y*dt/self.__mass[1]
        self.__pos[0][0] += self.__vel[0][0]*dt
        self.__pos[1][0] += self.__vel[1][0]*dt
        self.__pos[1][0] += self.__vel[1][0]*dt
        self.__pos[1][1] += self.__vel[1][1]*dt

        # for i in range(self._led.numLEDs):
        #     self._led.set(i, rgb)
        #     total_mA += self.__rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        # print self.__total_Ah / (self._led.numLEDs*self.__rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))
        # print total_mA

        # Increment the internal step by the given amount
        self._step += amt
