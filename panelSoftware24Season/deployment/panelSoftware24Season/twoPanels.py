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




def main():
    #time.sleep(1)
    ################
    global triggerRate
    triggerRate = 300

    global useGPIO
    useGPIO = 1
    ##################

    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--trigRate', dest='trigRate', type=int, default=0)
    args = ap.parse_args()

    if args.trigRate !=0:
        triggerRate = args.trigRate

    print(f'running both panels with trigger rate {triggerRate}')
    

    #kill any open gpio monitor processes
    command = 'pkill -f gpio'
    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid
    )

    sys.stderr = open('err.txt', 'w')
    global p1
    global p2
    global panel1
    global panel2
    panel1 = os.environ['panel1']
    panel2 = os.environ['panel2']

    hit.powerCycle()
    time.sleep(1)
    hit.panelStartup()
    time.sleep(2)
    #panel1Temp = hit.getPanelTemp(panel1)
    #panel2Temp = hit.getPanelTemp(panel2)

    #print(f'temps are {panel1Temp} and {panel2Temp}')
    #settingsList1 = hit.getThresholdAndVoltageNew(panel1,panel1Temp,triggerRate)
    #settingsList2 = hit.getThresholdAndVoltageNew(panel2,panel2Temp,triggerRate)

    print(triggerRate)
    p1 = start1(triggerRate)
    p2 = start2(triggerRate)
    
    signal.signal(signal.SIGINT, signal_handler)
    now = datetime.now()
    print(now)

    #nextDay = now+ timedelta(days= 10)
    #print(nextDay)

    logFile = open("2PanelTestLog.txt","w")
    
    #while datetime.now() < nextDay:
    while True:
        time.sleep(10)
        
        if p1.is_alive() and p2.is_alive():
            continue
            #time.sleep(2)
            #print('\n\nboth alive\n\n')
            #essage = f'both alive'
            #logFile.write(str(time.time_ns()) + ',' + message+'\n')

        else:
            print('\n\n\n\nprocess dead\n\n\n\n')
            message = f'process dead'
            
            logFile.write(str(time.time_ns()) + ',' + message+'\n')
            print(f'p1 {p1.is_alive()}')
            print(f'p2 {p2.is_alive()}')
            restart(p1,p2)
            time.sleep(.5)
            p1 = start1(triggerRate)
            time.sleep(.1)
            p2 = start2(triggerRate)
        


def start1(triggerRate):

    

    process = Process(
        target=singlePanelHitBufferMode.main,args=(panel1,0,0,triggerRate,useGPIO)
    )
    process.daemon = True
    process.start()
    #process.join()
    print(f'process pid is {process.pid}')
    return process
    
def start2(triggerRate):
    
    process1 = Process(
        target=singlePanelHitBufferMode.main,args=(panel2,0,0,triggerRate,useGPIO)
    )
    process1.daemon = True
    process1.start()
    #process1.join()
    print(f'process pid is {process1.pid}')
    return process1

def restart(p1,p2):
    if p1.is_alive():
        os.kill(p1.pid, signal.SIGINT)
    if p2.is_alive():
        os.kill(p2.pid, signal.SIGINT)
    timeOff = time.time_ns()
    
    #time.sleep(.5)
    p1.terminate()
    p2.terminate()

    command = 'pkill -f gpio'
    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid
    )

    while True:
        print("\n\n\npower cycling\n\n\n")
        hit.powerCycle()
        time.sleep(.3)
        panelStart = hit.panelStartup()
        if panelStart ==1:
            time.sleep(.3)
            break
    powerCycleLogger(timeOff)


def powerCycleLogger(startTime):
    errFile = open("powerCycleLog.txt","a")
    message = f'Power cycled the panels here'
    errFile.write(f'{startTime},{str(time.time_ns())}\n')
    errFile.close()
   


def signal_handler(sig, frame):
    print(f'main program stop command issued, closing files and shutting down')
    
    print('moving to process alive checks')
    print(p1.pid,p2.pid,p1.is_alive(),p2.is_alive())
    if p1.is_alive():
        print('killing p1')
        #os.killpg(os.getpgid(p1.pid), signal.SIGINT)
        os.kill(p1.pid, signal.SIGINT)
        
        
    if p2.is_alive():
        #os.killpg(os.getpgid(p2.pid), signal.SIGINT)
        os.kill(p2.pid, signal.SIGINT)
        
        print('killing p2')

    p1.join()
    p2.join()

    command = 'pkill -f gpio'
    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid
    )
    time.sleep(2)
    
    sys.exit(0)
    

if __name__ == "__main__":
    main()