#!/usr/bin/env python3

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




#TO DO: write in a power cycler for this to ensure all the thresholds get read


def main():
    
    hit.testFunction(2000)
    runTime = 10

    
    

   
    
    panel1 = os.environ['panel1']
    panel2 = os.environ['panel2']

    serNone =  serial.Serial()
    panel1Temp = hit.getPanelTemp(panel1,serNone)
    serNone =  serial.Serial()
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
    p1FileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel1TempDir}/{mydate}/histogramRuns'
    p2FileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel2TempDir}/{mydate}/histogramRuns'
    print(p1Filename)
    #print(p2FileDir)
    
    if os.path.isfile(p1Filename):
        with open(p1Filename) as f1:
            inList = f1.readlines()
            #for i in inList:
                #print(i)
            nThreshRan = len(inList)-1
            lastThresh = int(inList[-1].split(',')[1])
            print(lastThresh, nThreshRan)
        
    else:
        lastThresh = 2800
        nThreshRan = 0




    for i in range(1,30-nThreshRan):
        threshold= lastThresh - i*10
        #threshold= 2000 - i*10 #lab value
        print(f'threshold value for run is {threshold}')
        #print(f'running panels at voltage setting {voltage} threshold {threshold} for {runTime} seconds\n')
        try:
            p1dir_list_start = os.listdir(p1FileDir)
            p2dir_list_start = os.listdir(p2FileDir)
        except:
            p1dir_list_start = []
            p2dir_list_start = []
        p1StartFiles=0
        p2StartFiles=0
        for j in p1dir_list_start:
                if str(f'panel{panel1}') in j:
                    p1StartFiles+=1

        for j in p2dir_list_start:
            if str(f'panel{panel2}') in j:
                p2StartFiles+=1
    

            
        p1th = Process(
        target=hm.main,args=(0,panel1,threshold,panel1Voltage,runTime,p1Filename)
        )
        p1th.daemon = False
        p2th = Process(
        target=hm.main,args=(0,panel2,threshold,panel2Voltage,runTime,p2Filename)
        )
        p2th.daemon = False

        p1th.start()
        p2th.start()
        p1th.join()
        p2th.join()
        
        if p1th.is_alive():
            os.kill(p1th.pid, signal.SIGINT)
        if p2th.is_alive():
            os.kill(p2th.pid, signal.SIGINT)


        p1dir_list = os.listdir(p1FileDir)
        p2dir_list = os.listdir(p2FileDir)

        #p1dir_list.sort()
        p1NumFiles=0
        p2NumFiles=0
        for j in p1dir_list:
            if str(f'panel{panel1}') in j:
                p1NumFiles+=1

        for j in p2dir_list:
            if str(f'panel{panel2}') in j:
                p2NumFiles+=1

        
          

        
        #check if both files written ( files written at end of histogram.main() )
        print(f'panel {panel1} number of files at start {p1StartFiles} number after run try {(p1NumFiles)}')
        print(f'panel {panel2} number of files at start {(p2StartFiles)} number after run try {(p2NumFiles)}')

    statusDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel1TempDir}/{mydate}'
    #readTempFile = os.path.join(tempDir, temp_dir_list[0])
    with open(f'{statusDir}/status.txt', 'w') as f:
        f.write(f'{time.time_ns} sweeps completed')

    statusDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel2TempDir}/{mydate}'
    #readTempFile = os.path.join(tempDir, temp_dir_list[0])
    with open(f'{statusDir}/status.txt', 'w') as f:
        f.write(f'{time.time_ns} sweeps completed')


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