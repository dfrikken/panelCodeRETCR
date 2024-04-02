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

    p1 = start1()
    p2 = start2()

    #time.sleep(10)
  
    #restart(p1,p2)


    #p1 = start1()
    #p2 = start2()


    
    while True:
        if p1.is_alive() and p2.is_alive():
            #print('\n\nboth alive\n\n')
            time.sleep(10)

        else:
            print('\n\n\n\nprocess dead\n\n\n\n')
            print(f'p1 {p1.is_alive()}')
            print(f'p2 {p2.is_alive()}')
            restart(p1,p2)
            time.sleep(1)
            p1 = start1()
            time.sleep(.1)
            p2 = start2()

    
    
    
    '''
  
 

   
    print('im here')
    print(f'p1 {p1.is_alive()}')
    print(f'p2 {p2.is_alive()}')
    print(f'p1 {p1.pid}')
    print(f'p2 {p2.pid}')

    time.sleep(10)

    os.kill(p1.pid, signal.SIGINT)
    os.kill(p2.pid, signal.SIGINT)

    print(f'p1 {p1.is_alive()}')
    print(f'p2 {p2.is_alive()}')

    time.sleep(.1)
    p1.terminate()
    p2.terminate()
    
    

    
    while True:
        if process1.is_alive() and process.is_alive():
            print('both alive')
            time.sleep(5)

        else:
            print('process dead')
            print(f'p1 {process.is_alive()}')
            print(f'p2 {process1.is_alive()}')
            time.sleep(2)

    
    process = Process(
        target=testProgram,args=(1,'test1','testing logger',0)
    )

    process1 = Process(
        target=testProgram,args=(6,'test2','testing logger',1)
    )

    process.start()
    process1.start()
    process.join()
    process1.join()



    
    for i in range(1):
        port0Thread = Thread(target=runProgram, args=(0,1500,))
        port1Thread = Thread(target=runProgram, args=(1,1500,))

        threads = [port0Thread,port1Thread]
        
        print(f'starting coincidence run {i+1}')
        for t in threads:
            t.start()

    # Wait for all threads to finish.
        #for t in threads:
        #    t.join()

        #print('here')
        nRun = 1
        while True:
            
            #print(port0Thread.is_alive())
            #print(port1Thread.is_alive())
            
            time.sleep(1)
            
            if port0Thread.is_alive() == False or port1Thread.is_alive()==False:
                print('here')
                print(f'port 0 {port0Thread.is_alive()}')
                print(f'port 1 {port1Thread.is_alive()}')
                #os.killpg(port0Thread.ident, signal.SIGINT)

                #pthread_kill(port0Thread.ident, SIGTSTP)
                #pthread_kill(port1Thread.ident, SIGTSTP)
                print(f'port 0 {port0Thread.is_alive()}')
                print(f'port 1 {port1Thread.is_alive()}')
                #break
                #port0Thread = Thread(target=runProgram, args=(0,1500,))
                #port1Thread = Thread(target=runProgram, args=(1,1500,))

                #threads = [port0Thread,port1Thread]
                
                #print(f'starting coincidence run {nRun+1}')
                #nRun+=1
                #for t in threads:
                #    t.start()
        #time.sleep(30)
    
    
    
    
    '''
    sys.exit()
    #return 0

def start1():
    process = Process(
        target=piTesting.main,args=(0,1600,2600)
    )
    process.start()
    return process
    

def start2():
    process1 = Process(
        target=piTesting.main,args=(1,1600,2600)
    )
    process1.start()
    return process1

def restart(p1,p2):
    if p1.is_alive():
        os.kill(p1.pid, signal.SIGINT)
    if p2.is_alive():
        os.kill(p2.pid, signal.SIGINT)
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

if __name__ == "__main__":
    main()