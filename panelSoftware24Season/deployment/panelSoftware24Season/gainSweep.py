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

def main(tempDir,startVoltage=2800,nRuns=10):

    runTime = 30
    threshold = 1500

    panel1 = os.environ['panel1']
    panel2 = os.environ['panel2']

    panel1Temp = hit.getPanelTemp(panel1)
    panel2Temp = hit.getPanelTemp(panel2)

    normFilePath = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'

    dir_list = os.listdir(normFilePath)

    fileList = []
    for i in dir_list:
        fileList.append(i)
        bottom = int(i.split('_')[0])
        top = int(i.split('_')[1])
        if panel1Temp in range(bottom,top):
            #print(i)
            tempDir = i
            tempRange = i
            break
    
    panel1TempDir = os.path.join(normFilePath, tempDir)


    fileList = []
    for i in dir_list:
        fileList.append(i)
        bottom = int(i.split('_')[0])
        top = int(i.split('_')[1])
        if panel2Temp in range(bottom,top):
            #print(i)
            tempDir = i
            tempRange = i
            break
    
    panel2TempDir = os.path.join(normFilePath, tempDir)
    
    print(f'panel 1 temp is {panel1Temp} using {panel1TempDir}')
    print(f'panel 2 temp is {panel2Temp} using {panel2TempDir}')

    mydatetime = datetime.now()
    mydate = str(mydatetime.date())

    p1Filename = makeFile(panel1,mydate,panel1TempDir)
    p2Filename = makeFile(panel2,mydate,panel2TempDir)
    print('files made, running histogram mode for gain sweep')
    
    for i in range(nRuns):
        voltage = startVoltage - i*5
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
    

def makeFile(panel,mydate,tempDir):
    runDir = f'runs/normalizationRuns/{tempDir}/{mydate}/voltageSweeps'
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