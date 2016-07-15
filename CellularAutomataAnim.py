# Copyright 2016 Martin Roth (mhroth@gmail.com). All Rights Reserved.

sys.path.append(os.path.abspath("../BiblioPixel"))
from bibliopixel.led import *
from bibliopixel.animation import *
from bibliopixel.drivers.serial_driver import *
from bibliopixel.drivers.visualizer import *
from bibliopixel.gamma import *

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
