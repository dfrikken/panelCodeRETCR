#!/usr/bin/env python


import sys
import os
import argparse
import time
import glob
import serial
from datetime import datetime, timedelta
import json
from cobs import cobs
import hitBufferDefine as hit
import numpy as np
import signal
from threading import Thread
import singlePanelHitBufferMode as singlePanelHitBufferMode
import subprocess
from subprocess import PIPE, Popen

from multiprocessing import Process

################
global triggerRate
triggerRate = 100

global useGPIO
useGPIO = 0
##################


def main():
    hit.testFunction(300)
    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
    here = os.path.dirname(path)

    for i in range(-40,10):
        if i%5 ==0:
            print(f'{i}_{i+5}')
            dirName = f'{i}_{i+5}'
            if not os.path.exists(os.path.join(here, dirName)):
                os.makedirs(os.path.join(here, dirName))


if __name__ == "__main__":
    main()