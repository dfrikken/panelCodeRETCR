#!/usr/bin/env python

'''
This is the primary data taking script for the panels in the 24 RET-CR season

functions are defined in hitBufferDefine.py 
    imported as hit so use is hit.testFunction()

'''



import sys
import os
import argparse
import time
import glob
import serial
import datetime
import json
from cobs import cobs
import hitBufferDefine as hit
import numpy as np


 
ap = argparse.ArgumentParser()
ap.add_argument('-t', '--time', dest='runtime', type=int, default=3,
                help='data acquisition time in seconds (default is 10 seconds)')
ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2600,
                help='voltage setting in daq units (default is 2650)')
ap.add_argument('-d', '--disc', dest='disc', type=int, default=1710,
                help='discriminator setting in daq units (default is 1390)')
ap.add_argument('-p','--port',dest="PORT",type=int,default=0)
args = ap.parse_args()
PORT = '/dev/ttyUSB' + str(args.PORT)


# voltage sanity check
if args.voltage > 2900:
    print('ERROR: voltage setting should never need to be >2800')
    sys.exit()

# connect to udaq via USB
try:
    ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN)
    ser.timeout = 1
    ser.flushInput()
    ser.flushOutput()
except:
    print("ERROR: is the USB cable connected?")
    #sys.exit() #commented for testing
print('serial connection made')


# reset the uDAQ to clear anything that lingers
#hit.resetUDaq()

#schedule trigs to latch udaq time to rpi with gpio monitor
hit.scheduleTriggers()
    
# initialize the adcs, set voltage, threshold, etc.
#hit.init(args)


#data is the list the buffer is read into, this is dumped into the .bin file
data = []

'''
#setup the cpu trig and trigger mode parameters
hit.cmdLoop('set_cputrig_10mhz_enable 1',ser) 
hit.cmdLoop('set_cputrig_enable 1',ser) 
#cmdLoop('trigout_width 10',ser)
hit.cmdLoop('trigout_mode 2',ser) # 2 = trigger formed during buffer readout





print(args)
hit.testFunction()
for j in range(3):
    rundir, runfile = hit.getNextRun(1,"/Users/frikken.1/documents/ret/retcr24")
    print(runfile)
    for i in range(5):
        t = np.uint64(time.time_ns())
        time.sleep(.40000)
        t2 = np.uint64(time.time_ns())
        hit.deadTimeAppend(t,t2,rundir)
'''








