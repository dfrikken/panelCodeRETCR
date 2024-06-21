#!/usr/bin/env python3


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
    #hit.testFunction(3000)
    '''
    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
    here = os.path.dirname(path)

    for i in range(-40,10):
        if i%5 ==0:
            #print(f'{i}_{i+5}')
            dirName = f'{i}_{i+5}'
            if not os.path.exists(os.path.join(here, dirName)):
                os.makedirs(os.path.join(here, dirName))
    
    '''
    dir = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/-25_-20'
    panel = os.environ['panel1']
    set1 = hit.fitMipLinear(panel, dir)
    set2 = hit.readMipFile(panel,dir)
    hit.fitThreshCurve(panel,dir)
    print(set1,set2)
    panel = os.environ['panel2']
    set1 = hit.fitMipLinear(panel, dir)
    set2 = hit.readMipFile(panel,dir)
    hit.fitThreshCurve(panel,dir)
    print(set1,set2)
    '''
    startTime = time.time_ns()
    hit.powerCycle()
    #time.sleep(.5)
    hit.panelStartup()
    time.sleep(.5)
    endTime = time.time_ns()
    panel = str(12)
    ser = serial.Serial()
    temp = hit.getPanelTemp(panel, ser)
    temp = hit.getPanelTemp(panel, ser)
    print(f'time to power cycle is {(endTime - startTime)/1e9}')
    
    '''
  
    #hit.getThresholdAndVoltageSingle(panel,temp,300)
    #settingsList = hit.getThresholdAndVoltageNew(panel,temp,300)
    #ser = serial.Serial()
    #temp = hit.getPanelTemp(3, ser)
    #hit.getThresholdAndVoltageNew(3,temp,300)


if __name__ == "__main__":
    main()