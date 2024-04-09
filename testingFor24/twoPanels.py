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

from multiprocessing import Process


def main():
    sys.stderr = open('err.txt', 'w')
    global p1
    global p2
    p1 = start1()
    p2 = start2()
    
    signal.signal(signal.SIGINT, signal_handler)
    now = datetime.now()
    print(now)

    nextDay = now+ timedelta(days= 2)
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
            p1 = start1()
            time.sleep(.1)
            p2 = start2()
            

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


def start1():
    process = Process(
        target=piTesting.main,args=(12,1560,2622)
    )
    process.daemon = True
    process.start()
    #process.join()
    print(f'process pid is {process.pid}')
    return process
    
def start2():
    process1 = Process(
        target=piTesting.main,args=(3,1570,2601)
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