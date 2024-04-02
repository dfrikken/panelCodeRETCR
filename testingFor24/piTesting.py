#!/usr/bin/env serialpython


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

#global serialPort
#hit.testFunction()

subrunTime = 60

def main(port = 0, disc = 1700, voltage = 2650):
#def main():
    
    #arguments for the run
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--time', dest='runtime', type=int, default=3)
    ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2650)
    ap.add_argument('-d', '--disc', dest='disc', type=int, default=1710)
    ap.add_argument('-p','--port',dest="PORT",type=int,default=0)
    args = ap.parse_args()

    
    args.PORT = port
    args.disc = disc
    args.voltage = voltage
    
    
   

    PORT = '/dev/ttyUSB' + str(args.PORT) #changing to the UART ID in the future
    


    #print(disc, args.disc)
    print(args)
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
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN, timeout=3)
       #ser.timeout = 1
        ser.flushInput()
        ser.flushOutput()
    except:
        print("ERROR: is the USB cable connected?")
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing
    print('serial connection made')
    signal.signal(signal.SIGINT, signal_handler)
    global serialPort
    serialPort = ser

    panel = hit.panelIDCheck(ser)
    #logDirectory = hit.changeGlobals(f'panel{panel}Logs/')
    #print(f'panel {panel} log directory for run is {logDirectory}')

    for run in range(12):
        startTime = datetime.now()
        print(f'\n\npanel {panel} start of run = {startTime}')
        nextHour = startTime.replace(minute = 0,second=0, microsecond=0)+ timedelta(hours=1)
        print(f'panel {panel} end of run = {nextHour}')
        n = 0

        print(f'panel {panel} time to end of run {(nextHour - startTime).total_seconds()} seconds')
    
        rundir, runfile = hit.getNextRun(panel,"runs") 
        print(f'panel {panel} run file is {runfile}')
        #print(rundir)
        logDirectory = hit.changeGlobals(f'{rundir}/logs/',ser)
        print(logDirectory)

        #hit.makeJson(0,0,0,0,0) #checking that the error logging works

        hit.makeJson(ser,subrunTime,args, rundir, runfile)

        #hit.init(ser,args)

        numScheduledTriggers = hit.scheduleTriggers(ser,pin,rundir,10)

        scheduledTriggerFlag = hit.gpioMon(pin,2,rundir,0,numScheduledTriggers,0)

        if( scheduledTriggerFlag ==0):
            print('retrying the scheduled triggers')
            numScheduledTriggers = hit.scheduleTriggers(ser,pin,rundir,10)
            scheduledTriggerFlag = hit.gpioMon(pin,3,rundir,0,numScheduledTriggers,0)

########################################
####### start the data run #############
########################################
        
        #open a thread for the gpio monitor 
        now = datetime.now()
        #gpioMonTime = subrunTime+3 #for testing
        gpioMonTime = round((nextHour - now).total_seconds() ,0)
        #print(f'panel {panel} gpioMonTime is {gpioMonTime}')
        gpioThread = Thread(target=hit.gpioMon, args=(pin,gpioMonTime,rundir,0,numScheduledTriggers,1,))
        gpioThread.start()
        
        
        #panel data setup
        data = [] #list to hold the data from the buffer dump
        #bfile = open(os.path.join(rundir, runfile+'.bin'), 'wb') # .bin file containing the panel data
        with open(os.path.join(rundir, runfile+'.bin'), 'wb') as bfile:
            #uDAQ setup for data run
            hit.init(ser,args)
            hit.cmdLoop('set_cputrig_10mhz_enable 1',ser) #latch cputrig to 10MHz, its default but paranoia ya know
            hit.cmdLoop('set_cputrig_enable 1',ser) # enable the cpu triggers, default but see above
            hit.cmdLoop('trigout_mode 2',ser) # 2 = trigger formed during buffer readout, 1 = no triggers formed outside active run, 0 = no triggers
            hit.cmdLoop('set_livetime_enable 1', ser) #enable the livetime (this is the run)
        
            ########
            #subruns
            ########    
            while(True):
                n+=1
                now = datetime.now()
                if(n==1):
                    print(f'panel {panel} {(now - startTime ).total_seconds()} seconds from start of run to data taking')
                remainingTime = (nextHour - now).total_seconds()
                if subrunTime+1 < remainingTime:
                    print(f'panel {panel} run {run} subrun {n} with {remainingTime} seconds to hour')
                    hit.infoLogger(f'run {run} subrun {n} with {remainingTime} seconds to hour')
                    hit.cmdLoop(f'run 1 3500 0', ser, 5) #enable "run" in this case a subrun. subrun lasts till 'stop_run' command issued
                    print(f'panel {panel} sleeping for {subrunTime} seconds to form the subrun')
                    time.sleep(subrunTime)  #sleep the python program while the uDAQ does its thing
                    out = hit.cmdLoop('stop_run', ser, 100) #stop the subrun to read the buffer out (deadtime for panel data, but still forming triggers to central)
                    hit.getRate(ser) # print the trigger rate with duration (duration here in case you overfill the buffer if duration != subrunTime then overwrite)
                    #nEvents = hit.getNEvents(ser)
                    #print(f'panel {panel} number events in buffer {nEvents}')
                    #dump panel data from buffer and write to the .bin
                    beginTime = time.time_ns()
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
                    
                    
                    endTime = time.time_ns()
                    hit.deadTimeAppend(beginTime, endTime, rundir)
                    print(f'panel {panel} buffer readout {(endTime - beginTime)/1e9} seconds')
                
                else:
                    now = datetime.now()
                    remainingTime = (nextHour - now).total_seconds()
                    #print('last subrun')
                    print(f'panel {panel} last subrun, sleeping for remaining time of {remainingTime} seconds')
                    
                    if remainingTime>5:
                        hit.cmdLoop(f'run 1 3500 0', ser, 5) #enable "run" in this case a subrun. subrun lasts till 'stop_run' command issued
                        print(f'panel {panel} sleeping for {remainingTime-1} seconds to form the last subrun')
                        time.sleep(math.floor(remainingTime-1))  #sleep the python program while the uDAQ does its thing
                        out = hit.cmdLoop('stop_run', ser, 100) #stop the subrun to read the buffer out (deadtime for panel data, but still forming triggers to central)
                        hit.getRate(ser) # print the trigger rate with duration (duration here in case you overfill the buffer if duration != subrunTime then overwrite)
                        #nEvents = hit.getNEvents(ser)

                        #dump panel data from buffer and write to the .bin
                        beginTime = time.time_ns()
                        if out is None:
                                print('no data in dump')
                                hit.errorLogger("error: no data in buffer")
                                #break

                        dump = hit.cmdLoop('dump_hits_binary', ser, ntry=5, decode=False) 
                        if dump is not None:
                            data.append(dump)
                            for dump in data:
                                bfile.write(hit.cobsDecode(dump))
                    
                    elif remainingTime>0:
                        print("sleeping to next run")
                        time.sleep(remainingTime)
                        print(f'panel {panel} wrote files to {runfile}')
                        break

                    elif remainingTime < 0: #just in case pythonic things happen
                        print(f'panel {panel} wrote files to {runfile}')
                        break



    #end the run and shutdown the uDAQ and its serial connection
    hit.closeSerial(ser)
    print('closing the serial port')
    

    '''
    #check for error logs and if there migrate to the run directory
        errFile = f'{logDirectory}errorLog.txt'
        check_file = os.path.isfile(errFile)
        if( check_file):
            print(f'panel {panel} moving error log to run directory {runfile}')
            #print(f'panel {panel} mv {errFile} {rundir}')
            hit.cmdline(f'mv {errFile} {rundir}')
    '''
   

    #print('sleeping to wait for the gpio monitor thread')
    #time.sleep(10)
    #print(f'panel {panel} {nEvents} in buffer')
    
    sys.exit()
    #return


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    hit.closeSerial(serialPort)
    print('closing the serial port')
    sys.exit(0)
    



if __name__ == "__main__":
    main()