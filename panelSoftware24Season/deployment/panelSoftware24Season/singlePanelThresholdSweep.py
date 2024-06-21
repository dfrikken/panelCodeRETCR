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



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--panel', dest='panel', type=str, default=12)
    args = ap.parse_args()
    hit.testFunction(2000)
    runTime = 10
    #panel=os.environ['panel1']
    panel = args.panel

   

    serNone =  serial.Serial()
    panelTemp = hit.getPanelTemp(panel,serNone)
    
    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
    dir_list = os.listdir(path)
    #print(dir_list)
    fileList = []
    for i in dir_list:
        fileList.append(i)
        bottom = int(i.split('_')[0])
        top = int(i.split('_')[1])
        if panelTemp in range(bottom,top):
            #print(i)
            tempDir = i
            tempRange = i
            break

    tempDir = os.path.join(path, tempDir)
    #temp_dir_list = os.listdir(tempDir)
    #print(tempDir)
    #print(tempRange)
    #dataDir = os.path.join(tempDir,temp_dir_list[0])
    panelTempDir = os.path.join(path, tempRange)
    #panelVoltage = hit.readMipFile(panel, tempDir)
    panelVoltage = hit.fitMipLinear(panel, tempDir)
    #print(panelTempDir)
    #print(panelVoltage)

    
    
    print(f'panel 1 temp is {panelTemp} using {panelTempDir}')





    
    mydatetime = datetime.now()
    mydate = str(mydatetime.date())

    #removing date from directory path 
    #panelFilename = makeFile(panel,mydate,tempRange)
    panelFilename = makeFile(panel,tempRange)
    #p2Filename = makeFile(panel2,mydate,panel2TempDir)
    #print(f'files made, running histogram mode for threshold sweep for temp range {tempDir}')
    panelFileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{tempRange}/histogramRuns'
    #p2FileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel2TempDir}/{mydate}/histogramRuns'
    #print(panelFilename)
    #print(p2FileDir)
    
    if os.path.isfile(panelFilename):
        with open(panelFilename) as f1:
            inList = f1.readlines()
            #for i in inList:
                #print(i)
            
            nThreshRan = len(inList)-1
            lastThresh = int(inList[-1].split(',')[1])
            print(lastThresh, nThreshRan)
        
    else:
        lastThresh = 2900
        nThreshRan = 0




    for i in range(1,60-nThreshRan):
        threshold= lastThresh - i*10
        #threshold= 2000 - i*10 #lab value
        print(f'threshold value for run is {threshold}')
        #print(f'running panels at voltage setting {voltage} threshold {threshold} for {runTime} seconds\n')
        try:
            paneldir_list_start = os.listdir(panelFileDir)
            #p2dir_list_start = os.listdir(p2FileDir)
        except:
            paneldir_list_start = []
            #p2dir_list_start = []
        panelStartFiles=0
        #p2StartFiles=0
        for j in paneldir_list_start:
                if str(f'panel{panel}') in j:
                    panelStartFiles+=1
        #print(panel,threshold,panelVoltage,runTime,panelFilename)
            
        p1th = Process(
        target=hm.main,args=(0,panel,threshold,panelVoltage,runTime,panelFilename)
        )
        p1th.daemon = True
    
        p1th.start()
        p1th.join()
     
        
        if p1th.is_alive():
            os.kill(p1th.pid, signal.SIGINT)
     


        paneldir_list = os.listdir(panelFileDir)
        

        #p1dir_list.sort()
        panelNumFiles=0
        
        for j in paneldir_list:
            if str(f'panel{panel}') in j:
                panelNumFiles+=1

  

        
          

        
        #check if both files written ( files written at end of histogram.main() )
        print(f'panel {panel} number of files at start {panelStartFiles} number after run try {(panelNumFiles)}')
        

    statusDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{tempRange}'

    #readTempFile = os.path.join(tempDir, temp_dir_list[0])
    print(f'writing status file at {statusDir}')
    with open(f'{statusDir}/status{panel}.txt', 'w') as f:
        f.write(f'{time.time_ns} sweeps completed')



def makeFile(panel,tempDir):
    mydatetime = datetime.now()
    mydate = str(mydatetime.date())
    runDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{tempDir}/thresholdSweeps'
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