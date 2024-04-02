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
import math

def main(port = 0):
    hit.testFunction()

    #hit.powerCycle()

    #hit.panelStartup()

    #time.sleep(.1)

    PORT = '/dev/ttyUSB'+ str(port)
    try:
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN, timeout=3)
        #ser.timeout = 1
        #ser.flushInput()
        #ser.flushOutput()
    except:
        print("ERROR: is the USB cable connected?")
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing
    print('serial connection made')


    panel = hit.panelIDCheck(ser)

    ser.close()
    
    '''
    time.sleep(.1)

    PORT = '/dev/ttyUSB1'
    try:
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN, timeout=3)
        #ser.timeout = 1
        #ser.flushInput()
        #ser.flushOutput()
    except:
        print("ERROR: is the USB cable connected?")
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing
    print('serial connection made')


    panel = hit.panelIDCheck(ser)
                
    
    
    '''
   


if __name__ == "__main__":
    main()