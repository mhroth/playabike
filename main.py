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

class CellularAutomataAnim(BaseStripAnim):
    def __init__(self, led, fps=None, gamma=None, tween_time=1, start=0, end=-1):
        #The base class MUST be initialized by calling super like this
        super(CellularAutomataAnim, self).__init__(led, start, end)
        #Create a color array to use in the animation
        self._colors = [colors.Red, colors.Orange, colors.Yellow, colors.Green, colors.Blue, colors.Indigo]

        if fps:
            self._internalDelay = int(1000.0/fps)

        self.__total_Ah = 0.0
        self.__gamma = gamma
        self.__tween_rate = int(fps * float(tween_time))

        # Rule 90
        # https://en.wikipedia.org/wiki/Rule_90
        # self.__ca_rules = {
        #     (0,0,0): 0,
        #     (0,0,1): 1,
        #     (0,1,0): 0,
        #     (0,1,1): 1,
        #     (1,0,0): 1,
        #     (1,0,1): 0,
        #     (1,1,0): 1,
        #     (1,1,1): 0
        # }

        # Rule 110
        # https://en.wikipedia.org/wiki/Rule_110
        # self.__ca_rules = {
        #     (0,0,0): 0,
        #     (0,0,1): 1,
        #     (0,1,0): 1,
        #     (0,1,1): 1,
        #     (1,0,0): 0,
        #     (1,0,1): 1,
        #     (1,1,0): 1,
        #     (1,1,1): 0
        # }

        # Rule 30
        # https://en.wikipedia.org/wiki/Rule_30
        self.__ca_rules = {
            (0,0,0): 0,
            (0,0,1): 1,
            (0,1,0): 1,
            (0,1,1): 1,
            (1,0,0): 1,
            (1,0,1): 0,
            (1,1,0): 0,
            (1,1,1): 0
        }

        # define CA state arrays
        # https://en.wikipedia.org/wiki/Elementary_cellular_automaton
        self.__current_state_index = 0
        self.__ca_state = [
            [0 for _ in range(led.numLEDs+2)],
            [0 for _ in range(led.numLEDs+2)]
        ]

        # define tween state
        self.__tween_state = [0 for _ in range(led.numLEDs+2)]

        # set initial state
        # for Sirpenski Triangle (Rule 90, 30)
        self.__ca_state[self.__current_state_index][int(led.numLEDs/2)] = 1

        # random start
        # for i in range(led.numLEDs+2):
        #     self.__ca_state[self.__current_state_index][i] = random.choice([0,1])

        # ensure toridal state (state wraps around the array)
        self.__ca_state[self.__current_state_index][0] = self.__ca_state[self.__current_state_index][led.numLEDs]
        self.__ca_state[self.__current_state_index][led.numLEDs+1] = self.__ca_state[self.__current_state_index][1]

        # update state once to get next state
        self.__update_ca_state()

    def __update_ca_state(self):
        old_state = self.__ca_state[self.__current_state_index]
        new_state = self.__ca_state[self.__current_state_index^1]
        self.__current_state_index ^= 1 # switch state
        for i in range(1,led.numLEDs+1):
            new_state[i] = self.__ca_rules[tuple(old_state[i-1:i+2])]
        new_state[0] = new_state[led.numLEDs]
        new_state[led.numLEDs+1] = new_state[1]

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        # Fill the strip, with each sucessive color
        total_mA = 0.0

        if (self._step % self.__tween_rate) == 0:
            self.__update_ca_state()

        tween_state = tween(
            self.__ca_state[self.__current_state_index^1], # old state
            self.__ca_state[self.__current_state_index], # current state
            self._step,
            self.__tween_rate,
            self.__tween_state)

        # update LED values
        for i in range(self._led.numLEDs):
            rgb = (int(255*tween_state[i]), int(255*tween_state[i]), int(255*tween_state[i]))
            self._led.set(i, rgb)
            total_mA += rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))

        # Increment the internal step by the given amount
        self._step += amt

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
            [0.0 for _ in range(led.numLEDs)],
            [0.0 for _ in range(led.numLEDs)]
        ]
        self.__wave_state_vel = [0.0 for _ in range(led.numLEDs)]

        # initialise simulation
        self.__wave_state_pos[self.__current_state_index][int(led.numLEDs/2)] = 1.0

        self.__mean_impulse_period_step = mean_impulse_period * fps

        # schedule the next impulse
        self.__schedule_next_impulse()

    def __schedule_next_impulse(self):
        d = max(1, int(random.expovariate(1.0/self.__mean_impulse_period_step)))
        self.__next_impulse = self._step + d

    # https://en.wikipedia.org/wiki/Wave_equation#Investigation_by_numerical_methods
    def __update_wave_state(self, c=1.0, dt=1.0):
        """ c: speed of propagation
        """
        old_pos = self.__wave_state_pos[self.__current_state_index]
        new_pos = self.__wave_state_pos[self.__current_state_index^1]
        self.__current_state_index ^= 1

        # i == 0
        a = (c*c) * (old_pos[1] - 2.0*old_pos[0])
        self.__wave_state_vel[0] += a * dt
        new_pos[0] = old_pos[0] + (self.__wave_state_vel[0] * dt)

        # 0 < i < led.numLEDs-1
        for i in range(1,led.numLEDs-1):
            a = (c*c) * (old_pos[i+1] + old_pos[i-1] - 2.0*old_pos[i]) # acceleration
            self.__wave_state_vel[i] += a * dt
            new_pos[i] = old_pos[i] + (self.__wave_state_vel[i] * dt)

        # i == led.numLEDs-1
        a = (c*c) * (old_pos[led.numLEDs-2] - 2.0*old_pos[led.numLEDs-1])
        self.__wave_state_vel[led.numLEDs-1] += a * dt
        new_pos[led.numLEDs-1] = old_pos[led.numLEDs-1] + (self.__wave_state_vel[led.numLEDs-1] * dt)

    def preRun(self, amt=1):
        self._led.all_off()
        self.__start_time = self._msTime()

    def step(self, amt=1):
        # Fill the strip, with each sucessive color
        total_mA = 0.0

        if self._step == self.__next_impulse:
            # set the impulse
            i = random.randint(0, led.numLEDs-1)
            self.__wave_state_pos[self.__current_state_index][i] = random.choice([-1.0, 1.0])
            self.__wave_state_vel[i] = 0.0
            self.__schedule_next_impulse()

        # update the wave simulation
        self.__update_wave_state(c=3.0, dt=(self._internalDelay/1000.0))

        current_pos = self.__wave_state_pos[self.__current_state_index]

        for i in range(self._led.numLEDs):
            ui = min(max(((current_pos[i]*0.5)+0.5), 0.0), 1.0) # clamp pos to [-1,1]
            rgb = (int(255*ui), int(255*ui), int(255*ui))
            self._led.set(i, rgb)
            total_mA += rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        # print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))

        # Increment the internal step by the given amount
        self._step += amt

#create driver for a 30 pixels
# https://github.com/ManiacalLabs/BiblioPixel/wiki/DriverSerial
# driver = DriverSerial(LEDTYPE.APA102, 5*30, SPISpeed=24, gamma=gamma.APA102)
driver = DriverVisualizer(5*30)

# https://github.com/ManiacalLabs/BiblioPixel/wiki/LEDStrip
led = LEDStrip(driver)

# anim = CellularAutomataAnim(led, fps=20, gamma=gamma.APA102, tween_time=4)
anim = WaveAnim(led, fps=20, gamma=gamma.APA102, mean_impulse_period=10.0)
anim.run()

# writing an animation
# https://github.com/ManiacalLabs/BiblioPixel/wiki/Writing-an-Animation
