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
from multiprocessing import Process
import subprocess
from subprocess import PIPE, Popen

def main(port = 0):
    hit.testFunction(300)

    arr = os.listdir('/dev/serial/by-id/')
    print(arr)
    id1 = arr[0]
    id2 = arr[1]

    print(id1,id2)

    

    PORT = '/dev/serial/by-id/'+ id1
	# connect to udaq via USB

    ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE,timeout=3,stopbits=1)
    ser.flushInput()
    ser.flushOutput()
    panel1 = hit.panelIDCheck(ser)
    print(f'panel {panel1} serial id is {id1}')
    
    ser.close()
    PORT = '/dev/serial/by-id/'+ id2
        # connect to udaq via USB
    
    ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE,timeout=3,stopbits=1)
    ser.flushInput()
    ser.flushOutput()
    panel2 = hit.panelIDCheck(ser)
    print(f'panel {panel2} serial id is {id2}')
    
    ser.close()
    
    print(panel1,id1)
    print(panel2,id2)

if __name__ == "__main__":
    main()