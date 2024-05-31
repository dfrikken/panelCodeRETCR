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
    
    hit.testFunction(3000)
    runTime = 10

    
    

   
    
    panel1 = os.environ['panel1']
    panel2 = os.environ['panel2']

    serNone =  serial.Serial()
    panel1Temp = hit.getPanelTemp(panel1,serNone)
    panel2Temp = hit.getPanelTemp(panel2,serNone)

    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
    dir_list = os.listdir(path)
    #print(dir_list)
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

    tempDir = os.path.join(path, tempDir)
    temp_dir_list = os.listdir(tempDir)
    #print(tempDir)
    dataDir = os.path.join(tempDir,temp_dir_list[0])

    panel1Voltage = hit.readMipFile(panel1, dataDir)

    dir_list = os.listdir(path)
    #print(dir_list)
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

    tempDir = os.path.join(path, tempDir)
    temp_dir_list = os.listdir(tempDir)
    #print(tempDir)
    dataDir = os.path.join(tempDir,temp_dir_list[0])

    panel2Voltage = hit.readMipFile(panel2,dataDir)
    print(panel1Voltage,panel2Voltage)

    

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
    panel1TempDir = tempDir
    #panel1TempDir = os.path.join(normFilePath, tempDir)


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
    
    panel2TempDir = tempDir
    #panel2TempDir = os.path.join(normFilePath, tempDir)
    
    print(f'panel 1 temp is {panel1Temp} using {panel1TempDir}')
    print(f'panel 2 temp is {panel2Temp} using {panel2TempDir}')




    
    mydatetime = datetime.now()
    mydate = str(mydatetime.date())

    p1Filename = makeFile(panel1,mydate,panel1TempDir)
    p2Filename = makeFile(panel2,mydate,panel2TempDir)
    #print(f'files made, running histogram mode for threshold sweep for temp range {tempDir}')
    
    for i in range(30):
        threshold= 3000 - i*10
        #threshold= 2000 - i*10 #lab value
        print(f'threshold value for run is {threshold}')
        #print(f'running panels at voltage setting {voltage} threshold {threshold} for {runTime} seconds\n')
        
        
        p1 = Process(
        target=hm.main,args=(0,panel1,threshold,panel1Voltage,runTime,p1Filename)
        )
        p1.daemon = True
        p2 = Process(
        target=hm.main,args=(0,panel2,threshold,panel2Voltage,runTime,p2Filename)
        )
        p2.daemon = True

        p1.start()
        p2.start()
        p1.join()
        p2.join()
    
        
    

def makeFile(panel,mydate,tempDir):
    runDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{tempDir}/{mydate}/thresholdSweeps'
    #runDir = f'runs/normalizationRuns/{tempDir}/{mydate}/thresholdSweeps'
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, runDir)):
        rateFileName = f'{runDir}/panel{panel}ThresholdSweep_{mydate}.txt'
        #print(rateFileName)

    else:
        #print('directory doesnt exist')
        os.makedirs(os.path.join(here, runDir))
        rateFileName = f'{runDir}/panel{panel}ThresholdSweep_{mydate}.txt'
        #print(rateFileName)
    return rateFileName   

if __name__ == "__main__":
    main()