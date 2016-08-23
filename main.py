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
from CellularAutomataAnim import CellularAutomataAnim
from GravityAnim import GravityAnim
from StripTest import StripTest

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

#create driver
# https://github.com/ManiacalLabs/BiblioPixel/wiki/DriverSerial
driver = DriverSerial(LEDTYPE.APA102, 5*32, SPISpeed=24, gamma=gamma.APA102)
# driver = DriverVisualizer(5*32)

# https://github.com/ManiacalLabs/BiblioPixel/wiki/LEDStrip
led = LEDStrip(driver)

# anim = CellularAutomataAnim(led, fps=20, gamma=gamma.APA102, tween_time=0.4)
# anim = WaveAnim(led, fps=20, gamma=gamma.APA102, mean_impulse_period=30.0)
anim = LorenzAnim(led, fps=45, gamma=gamma.APA102)
# anim = StripTest(led, fps=4)
# anim = GravityAnim(led, fps=60, gamma=gamma.APA102)
anim.run()

# writing an animation
# https://github.com/ManiacalLabs/BiblioPixel/wiki/Writing-an-Animation
