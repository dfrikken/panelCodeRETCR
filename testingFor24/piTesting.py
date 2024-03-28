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

#temp imports
import random


#hit.testFunction()

subrunTime = 10


def main():

    #arguments for the run
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--time', dest='runtime', type=int, default=3)
    ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2650)
    ap.add_argument('-d', '--disc', dest='disc', type=int, default=1710)
    ap.add_argument('-p','--port',dest="PORT",type=int,default=0)
    args = ap.parse_args()
    PORT = '/dev/ttyUSB' + str(args.PORT) #changing to the UART ID in the future

    pin = 17 #default on port 0 
    if(args.PORT !=0):
        pin = 22
    
    print(f'pin = {pin}')



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
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing
    print('serial connection made')


    panel = hit.panelIDCheck(ser)
    
    rundir, runfile = hit.getNextRun(panel,"runs") 
    print(f'run file is {runfile}')

    hit.makeJson(ser,subrunTime,args, rundir, runfile)

    hit.init(ser,args)

    numScheduledTriggers = hit.scheduleTriggers(ser,1,rundir,10)

    scheduledTriggerFlag = hit.gpioMon(pin,3,rundir,0,numScheduledTriggers,0)

    if( scheduledTriggerFlag ==0):
        numScheduledTriggers = hit.scheduleTriggers(ser,1,rundir,10)
        scheduledTriggerFlag = hit.gpioMon(pin,3,rundir,0,numScheduledTriggers,0)

########################################
####### start the data run #############
########################################
    
    #open a thread for the gpio monitor 
    gpioThread = Thread(target=hit.gpioMon, args=(pin,subrunTime+2,rundir,0,numScheduledTriggers,1,))
    gpioThread.start()

    
    #panel data setup
    data = [] #list to hold the data from the buffer dump
    bfile = open(os.path.join(rundir, runfile+'.bin'), 'wb') # .bin file containing the panel data

    #uDAQ setup for data run
    hit.init(ser,args)
    hit.cmdLoop('set_cputrig_10mhz_enable 1',ser) #latch cputrig to 10MHz, its default but paranoia ya know
    hit.cmdLoop('set_cputrig_enable 1',ser) # enable the cpu triggers, default but see above
    hit.cmdLoop('trigout_mode 2',ser) # 2 = trigger formed during buffer readout, 1 = no triggers formed outside active run, 0 = no triggers
    hit.cmdLoop('set_livetime_enable 1', ser) #enable the livetime (this is the run)

    #subrun 
    hit.cmdLoop(f'run 1 3500 0', ser, 5) #enable "run" in this case a subrun. subrun lasts till 'stop_run' command issued
    print(f'sleeping for {subrunTime} seconds to form the subrun')
    time.sleep(subrunTime)  #sleep the python program while the uDAQ does its thing
    out = hit.cmdLoop('stop_run', ser, 100) #stop the subrun to read the buffer out (deadtime for panel data, but still forming triggers to central)
    hit.getRate(ser) # print the trigger rate with duration (duration here in case you overfill the buffer if duration != subrunTime then overwrite)
    nEvents = hit.getNEvents(ser)
    #dump panel data from buffer and write to the .bin
    if out is None:
            print('no data in dump')
            hit.errorLogger("error: no data in buffer")
            #break

    dump = hit.cmdLoop('dump_hits_binary', ser, ntry=5, decode=False) 
    if dump is not None:
        data.append(dump)
        for dump in data:
            bfile.write(hit.cobsDecode(dump))

    data = [] #reset the data list, we've done without but should keep the python programs memory down



    #end the run and shutdown the uDAQ and its serial connection
    hit.closeSerial(ser)
    print('closing the serial port')
    print(f'wrote files to {runfile}')

    #check for error logs and if there migrate to the run directory
    errFile = 'logs/errorLog.txt'
    check_file = os.path.isfile(errFile)
    if( check_file):
        print(f'moving error log to run directory {runfile}')
        #print(f'mv {errFile} {rundir}')
        hit.cmdline(f'mv {errFile} {rundir}')

    #print('sleeping to wait for the gpio monitor thread')
    #time.sleep(10)
    print(f'{nEvents} in buffer')
    return





if __name__ == "__main__":
    main()