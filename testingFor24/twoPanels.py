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
import piTesting
import subprocess
from subprocess import PIPE, Popen

from multiprocessing import Process

################
global triggerRate
triggerRate = 100
##################


def main():
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
    settingsList1 = hit.getThresholdAndVoltage(12,triggerRate)
    settingsList2 = hit.getThresholdAndVoltage(3,triggerRate)

    print(triggerRate)
    p1 = start1(settingsList1,triggerRate)
    p2 = start2(settingsList2,triggerRate)
    
    signal.signal(signal.SIGINT, signal_handler)
    now = datetime.now()
    print(now)

    nextDay = now+ timedelta(days= 10)
    print(nextDay)

    logFile = open("2PanelTestLog.txt","w")
    
    while datetime.now() < nextDay:
        
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
            time.sleep(1)
            p1 = start1(settingsList1,triggerRate)
            time.sleep(.1)
            p2 = start2(settingsList2,triggerRate)
            

    print("data taking test complete")
    logFile.write("data taking test complete\n")
    logFile.close()
    time.sleep(1)
    if p1.is_alive():
        
        os.kill(p1.pid, signal.SIGINT)
        p1.join()
        print('p1 killed')
        
    if p2.is_alive():
        
        os.kill(p2.pid, signal.SIGINT)
        p2.join()
        print('p2 killed')

    time.sleep(3)
    #p1.terminate()
    #p2.terminate()
    #sys.exit()
    return


def start1(settingsList,triggerRate):

    

    process = Process(
        target=piTesting.main,args=(12,settingsList[0],settingsList[1],triggerRate)
    )
    process.daemon = True
    process.start()
    #process.join()
    print(f'process pid is {process.pid}')
    return process
    
def start2(settingsList,triggerRate):
    settingsList = hit.getThresholdAndVoltage(3,triggerRate)
    process1 = Process(
        target=piTesting.main,args=(3,settingsList[0],settingsList[1],triggerRate)
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

    powerCycleLogger()
    time.sleep(.5)
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
        time.sleep(1)
        panelStart = hit.panelStartup()
        if panelStart ==1:
            time.sleep(1)
            break


def powerCycleLogger():
    errFile = open("powerCycleLog.txt","a")
    message = f'Power cycled the panels here'
    errFile.write(str(time.time_ns()) + ',' + message+'\n')
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
    time.sleep(2)
    
    sys.exit(0)
    

if __name__ == "__main__":
    main()