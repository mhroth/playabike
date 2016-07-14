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
        # self.__ca_rules = {
        #     (0,0,0): 0,
        #     (0,0,1): 1,
        #     (0,1,0): 1,
        #     (0,1,1): 1,
        #     (1,0,0): 1,
        #     (1,0,1): 0,
        #     (1,1,0): 0,
        #     (1,1,1): 0
        # }

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
        for i in range(1,led.numLEDs+1):
            rgb = (int(255*tween_state[i]), int(255*tween_state[i]), int(255*tween_state[i]))
            self._led.set(i-1, rgb)
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

        # 0 < i < led.numLEDs-1
        for i in range(1,led.numLEDs-1):
            a = K * (old_pos[i+1] + old_pos[i-1] - 2.0*old_pos[i]) # acceleration
            a -= L * self.__wave_state_vel[i] # damping force
            self.__wave_state_vel[i] += a * dt
            new_pos[i] = old_pos[i] + (self.__wave_state_vel[i] * dt)

        # i == led.numLEDs-1
        a = K * (old_pos[led.numLEDs-2] - 2.0*old_pos[led.numLEDs-1])
        a -= L * self.__wave_state_vel[led.numLEDs-1]
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
            total_mA += rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))

        # Increment the internal step by the given amount
        self._step += amt

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

            total_mA += rgb2mA(rgb, self.__gamma)
        self.__total_Ah += (total_mA * self._internalDelay / 3600000000.0)
        # print self.__total_Ah / (self._led.numLEDs*rgb2mA((255,255,255)) * ((self._msTime() - self.__start_time) / 3600000000.0))

        # Increment the internal step by the given amount
        self._step += amt

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
