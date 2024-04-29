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
from multiprocessing import Process
import subprocess
from subprocess import PIPE, Popen
import histogramMode as hm

def main():

    runTime = 30
    threshold = 1500

    panel1 = 12
    panel2 = 3
    

    mydatetime = datetime.now()
    mydate = str(mydatetime.date())

    p1Filename = makeFile(panel1,mydate)
    p2Filename = makeFile(panel2,mydate)
    print('files made, running histogram mode for gain sweep')
    
    for i in range(20):
        voltage = 2900 - i*5
        print(f'running panels at voltage setting {voltage}\n')
        
        
        p1 = Process(
        target=hm.main,args=(0,panel1,threshold,voltage,runTime,p1Filename)
        )
        p1.daemon = True
        p2 = Process(
        target=hm.main,args=(0,panel2,threshold,voltage,runTime,p2Filename)
        )
        p2.daemon = True

        p1.start()
        p2.start()
        p1.join()
        p2.join()
    
        
    

def makeFile(panel,mydate):
    runDir = f'runs/normalizationRuns/{mydate}/voltageSweeps'
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, runDir)):
        rateFileName = f'{runDir}/panel{panel}VoltageSweep_{mydate}.txt'
        #print(rateFileName)

    else:
        #print('directory doesnt exist')
        os.makedirs(os.path.join(here, runDir))
        rateFileName = f'{runDir}/panel{panel}VoltageSweep_{mydate}.txt'
        #print(rateFileName)
    
    return rateFileName

if __name__ == "__main__":
    main()