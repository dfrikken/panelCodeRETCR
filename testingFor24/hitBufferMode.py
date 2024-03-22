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
from datetime import datetime, timedelta
import json
from cobs import cobs
import hitBufferDefine as hit
import numpy as np

#temp imports
import random

 
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
    hit.errorLogger("error connecting to uDAQ over serial")
    #sys.exit() #commented for testing
print('serial connection made')




#schedule trigs to latch udaq time to rpi with gpio monitor
#hit.scheduleTriggers()
#time.sleep(5)

# reset the uDAQ to clear anything that lingers
#hit.resetUDaq()
    
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
'''



subrunTime = 27
#print(args)
#hit.testFunction()




for run in range(5):
    startTime = datetime.now()
    print(f'start of run = {startTime}')
    nextHour = startTime.replace(second=0, microsecond=0)+ timedelta(minutes=5)
    print(f'end of run = {nextHour}')
    n = 0
    rundir, runfile = hit.getNextRun(1,"/Users/frikken.1/documents/ret/retcr24")
    print(rundir, runfile)
    hit.makeJsonSpoof(subrunTime,args, rundir, runfile)
    gpioOut = hit.gpioMon(22,10,rundir)
    gpioFile = str(gpioOut[0]).split('\\n')[1].split(" ")[2]
    gpio = open(gpioFile,'r')
    print(f'{len(gpio.readlines())} scheduled triggers captured\n')
    gpio.close()

    
    while(True):
        n+=1
        now = datetime.now()
        remainingTime = (nextHour - now).total_seconds()
        if subrunTime < remainingTime:
            print(f'run {run} subrun {n} with {remainingTime} seconds to hour')
            print(f'sleeping for {subrunTime} seconds')
            time.sleep(subrunTime)
            print(f'\tsimulated subrun complete sleeping random time for buffer read')
            num = random.randrange(50,120)
            #print(num/100)
            beginTime = time.time_ns()
            time.sleep(num/100)
            endTime = time.time_ns()
            hit.deadTimeAppend(beginTime, endTime, rundir)
            print(f'\tbuffer read out to next subrun')
            print(f'\ttime elapsed {(datetime.now() - startTime).total_seconds()} ')
            print(" ")
        else:
            now = datetime.now()
            remainingTime = (nextHour - now).total_seconds()
            print(f'last subrun, sleeping for remaining time of {remainingTime} seconds')
            
            if remainingTime>5:
                print(f'\tsimulated subrun complete sleeping random time for buffer read')
                time.sleep(remainingTime-2)
                num = random.randrange(50,120)
                beginTime = time.time_ns()
                time.sleep(num/100)
                endTime = time.time_ns()
                hit.deadTimeAppend(beginTime, endTime, rundir)
                print(f'\ttime elapsed {(datetime.now() - startTime).seconds} seconds')
                print(datetime.now())
                now = datetime.now()
                remainingTime = (nextHour - now).total_seconds()
                print(f'remaining time to sleep {remainingTime}')
                time.sleep(remainingTime)
                print(" ")
                errFile = 'logs/errorLog.txt'
                check_file = os.path.isfile(errFile)
                if( check_file):
                    print(f'moving error log to run directory {runfile}')
                    #print(f'mv {errFile} {rundir}')
                    hit.cmdline(f'mv {errFile} {rundir}')
                break
            else:
                print("here")
                time.sleep(remainingTime)
                errFile = 'logs/errorLog.txt'
                check_file = os.path.isfile(errFile)
                if( check_file):
                    print(f'moving error log to run directory {runfile}')
                    #print(f'mv {errFile} {rundir}')
                    hit.cmdline(f'mv {errFile} {rundir}')
                break
            








'''
for j in range(3):
    rundir, runfile = hit.getNextRun(1,"/Users/frikken.1/documents/ret/retcr24")
    print(runfile)
    for i in range(5):
        t = np.uint64(time.time_ns())
        time.sleep(.40000)
        t2 = np.uint64(time.time_ns())
        hit.deadTimeAppend(t,t2,rundir)
'''










