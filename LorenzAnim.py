# Copyright 2016 Martin Roth (mhroth@gmail.com). All Rights Reserved.

import colorsys
import math
import os
import sys

sys.path.append(os.path.abspath("../BiblioPixel"))
from bibliopixel.led import *
from bibliopixel.animation import *
from bibliopixel.drivers.serial_driver import *
from bibliopixel.drivers.visualizer import *
from bibliopixel.gamma import *

class LorenzAnim(BaseStripAnim):
    def __init__(self, led, fps=None, gamma=None, start=0, end=-1):
        super(LorenzAnim, self).__init__(led, start, end)

        if fps:
            self._internalDelay = int(1000.0/fps)

        self.__x = 1
        self.__y = 1
        self.__z = 1

        self.__min = 100.0
        self.__max = -100.0

        self.__total_Ah = 0.0
        self.__gamma = gamma

    def __rgb2mA(self, rgb, gamma=None):
        """ Returns the number of milliamps used during this step
            for a given RGB tuple. Accounts for the given gamma correction.
        """
        if gamma:
            rgb = (gamma[x] for x in rgb)

        # assume 60mA at full brightness
        return (60.0/(255.0*3.0)) * sum(rgb)

    def __scale(self, x, i_start, i_end, o_start, o_end):
        y = (x-i_start)/(i_end-i_start)
        return (o_end-o_start)*y + o_start

    def __normal(self, m, s, num):
        # output is in range [0,1]
        return [math.exp(-((x-m)**2)/(2*s*s)) for x in range(num)]

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        # Fill the strip, with each sucessive color
        total_mA = 0.0

        dt=(self._internalDelay/1000.0)

        s = 10.0
        b = 8.0/3.0
        p = 28.0
        dx = s * (self.__y - self.__x)
        dy = (self.__x*(p - self.__z)) - self.__y
        dz = (self.__x*self.__y) - (b*self.__z)
        self.__x += (dx * dt)
        self.__y += (dy * dt)
        self.__z += (dz * dt)

        # print self.__x, self.__y, self.__z
        # print dx, dy, dz

        # if dz < self.__min:
        #     self.__min = dz
        # if dz > self.__max:
        #     self.__max = dz
        # print self.__min, self.__max

        # self._led.all_off()

        x = self.__scale(self.__x, -21, 23, 0, self._led.numLEDs-1)
        y = self.__scale(self.__y, -27, 31, 0, self._led.numLEDs-1)
        z = self.__scale(self.__z, 0, 58, 0, self._led.numLEDs-1)
        dx = self.__scale(abs(dx), 0, 297, 1, self._led.numLEDs/1)
        dy = self.__scale(abs(dy), 0, 643, 1, self._led.numLEDs/2)
        dz = self.__scale(abs(dz), 0, 490, 1, self._led.numLEDs/2)

        h = self.__normal(x, dx, self._led.numLEDs)
        s = self.__normal(y, dy, self._led.numLEDs)
        l = self.__normal(z, dz, self._led.numLEDs)

        for i in range(self._led.numLEDs):
            (r,g,b) = colorsys.hsv_to_rgb(h[i], s[i], l[i])
            rgb = (int(255*b),int(255*g),int(255*r))
            self._led.set(i, rgb)

            total_mA += self.__rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        # print self.__total_Ah / (self._led.numLEDs*self.__rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))
        print total_mA

        # Increment the internal step by the given amount
        self._step += amt
