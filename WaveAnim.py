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

class WaveAnim(BaseStripAnim):
    def __init__(self, led, fps, gamma=None, mean_impulse_period=10.0, start=0, end=-1):
        #The base class MUST be initialized by calling super like this
        super(WaveAnim, self).__init__(led, start, end)

        if fps:
            self._internalDelay = int(1000.0/fps)

        self.__total_Ah = 0.0
        self.__gamma = gamma

        # declare simulation memory
        self.__current_state_index = 0
        self.__wave_state_pos = [
            [0.0 for _ in range(self._led.numLEDs)],
            [0.0 for _ in range(self._led.numLEDs)]
        ]
        self.__wave_state_vel = [0.0 for _ in range(self._led.numLEDs)]

        # set next impulse to be immediately, to initialise simutlation
        self.__next_impulse = self._step

        self.__mean_impulse_period_step = mean_impulse_period * fps

    def __kToRgb(self, k):
        """ Converts color temperature in Kelvin to RGB value (1500K to 15000K).
        """
        # view-source:https://academo.org/demos/colour-temperature-relationship/demo.js?v=1454716371
        k = k / 100;

        if k <= 66:
            Red = 255;
        else:
            Red = k - 60
            Red = 329.698727466 * math.pow(Red, -0.1332047592)
            Red = min(255, max(0, Red))

        if k <= 66:
            Green = k
            Green = 99.4708025861 * math.log(Green) - 161.1195681661
            Green = min(255, max(0, Green))
        else:
            Green = k - 60
            Green = 288.1221695283 * math.pow(Green, -0.0755148492)
            Green = min(255, max(0, Green))

        if k >= 66:
            Blue = 255;
        else:
            if k <= 19:
                Blue = 0
            else:
                Blue = k - 10
                Blue = 138.5177312231 * math.log(Blue) - 305.0447927307
                Blue = min(255, max(0, Blue))

        rgb = (int(round(Red)), int(round(Green)), int(round(Blue)))
        return rgb

    def __scale(self, x, start, end):
        return (end-start)*x + start

    def __sigmoid(self, x, k=1.0):
        return 1.0 / (1.0 + math.exp(-1.0*k*x))

    def __schedule_next_impulse(self):
        d = max(1, int(random.expovariate(1.0/self.__mean_impulse_period_step)))
        self.__next_impulse = self._step + d

    def __rms(self, x):
        return math.sqrt(sum(i**2 for i in x)/len(x))

    def __rgb2mA(self, rgb, gamma=None):
        """ Returns the number of milliamps used during this step
            for a given RGB tuple. Accounts for the given gamma correction.
        """
        if gamma:
            rgb = (gamma[x] for x in rgb)

        # assume 60mA at full brightness
        return (60.0/(255.0*3.0)) * sum(rgb)

    # https://en.wikipedia.org/wiki/Wave_equation#Investigation_by_numerical_methods
    def __update_wave_state(self, K=5, L=0.1, dt=1.0):
        """ c: speed of propagation
        """
        K = K**2

        old_pos = self.__wave_state_pos[self.__current_state_index]
        new_pos = self.__wave_state_pos[self.__current_state_index^1]
        self.__current_state_index ^= 1

        # i == 0
        a = K * (old_pos[1] - 2.0*old_pos[0])
        a -= L * self.__wave_state_vel[0]
        self.__wave_state_vel[0] += a * dt
        new_pos[0] = old_pos[0] + (self.__wave_state_vel[0] * dt)

        # 0 < i < self._led.numLEDs-1
        for i in range(1,self._led.numLEDs-1):
            a = K * (old_pos[i+1] + old_pos[i-1] - 2.0*old_pos[i]) # acceleration
            a -= L * self.__wave_state_vel[i] # damping force
            self.__wave_state_vel[i] += a * dt
            new_pos[i] = old_pos[i] + (self.__wave_state_vel[i] * dt)

        # i == self._led.numLEDs-1
        a = K * (old_pos[self._led.numLEDs-2] - 2.0*old_pos[self._led.numLEDs-1])
        a -= L * self.__wave_state_vel[self._led.numLEDs-1]
        self.__wave_state_vel[self._led.numLEDs-1] += a * dt
        new_pos[self._led.numLEDs-1] = old_pos[self._led.numLEDs-1] + (self.__wave_state_vel[self._led.numLEDs-1] * dt)

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        # Fill the strip, with each sucessive color
        total_mA = 0.0

        if self._step == self.__next_impulse:
            # set the impulse
            i = random.randint(0, self._led.numLEDs-1)
            self.__wave_state_pos[self.__current_state_index][i] = random.choice([-1.0, 1.0])
            self.__wave_state_vel[i] = 0.0
            self.__schedule_next_impulse()

        # update the wave simulation
        self.__update_wave_state(K=2, L=0.05, dt=(self._internalDelay/1000.0))

        current_pos = self.__wave_state_pos[self.__current_state_index]

        for i in range(self._led.numLEDs):
            # ui = min(max(((current_pos[i]*0.5)+0.5), 0.0), 1.0) # clamp pos to [-1,1]
            # ui = min(1.0, max(-1.0, current_pos[i]))
            # ui = (ui+1)/2.0
            # https://academo.org/demos/colour-k-relationship/
            # if ui >= 0.0:
            #     ui = math.sqrt(ui)
            #     rgb = (int(107*ui), int(159*ui), int(255*ui))
            # else:
            #     ui = abs(ui)
            #     ui = math.sqrt(ui)
            #     rgb = (int(0*ui), int(165*ui), int(255*ui)) # 2300K

            ui = current_pos[i]
            if ui >= 0.0:
                # rgb = self.__kToRgb(1000)
                rgb = (255,95,0)
                ui = (self.__sigmoid(ui, 5) - 0.5) * 2.0
                rgb = (int(rgb[2]*ui), int(rgb[1]*ui), int(rgb[0]*ui))
            else:
                rgb = self.__kToRgb(1500)
                rgb = (0,195,255)
                ui = (self.__sigmoid(ui, 5) - 0.5) * -2.0
                rgb = (int(rgb[2]*ui), int(rgb[1]*ui), int(rgb[0]*ui))

            # ui = self.__sigmoid(ui, 5)
            # rgb = self.__kToRgb(self.__scale(ui, 1000, 2000))
            # rgb = (rgb[2], rgb[1], rgb[0])

            self._led.set(i, rgb)
            total_mA += self.__rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        # print self.__total_Ah / (self._led.numLEDs*self.__rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))
        print total_mA

        # Increment the internal step by the given amount
        self._step += amt
