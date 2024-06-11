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




def main(startVoltage=2800,nRuns=20):
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--panel', dest='panel', type=str, default=12)
    args = ap.parse_args()

    hit.testFunction(600)
    runTime = 30
    threshold = 1500

    panel1 = args.panel
    #panel1 = os.environ['panel1']
    #panel2 = os.environ['panel2']
    #print(panel1,type(panel1))

    serNone = serial.Serial()

    panel1Temp = hit.getPanelTemp(panel1,serNone)
    
    #serNone = serial.Serial()
    #panel2Temp = hit.getPanelTemp(panel2,serNone)

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
    
    #panel1TempDir = os.path.join(normFilePath, tempDir)
    panel1TempDir = tempDir


    print(f'panel 1 temp is {panel1Temp} using {panel1TempDir}')
    #print(f'panel 2 temp is {panel2Temp} using {panel2TempDir}')

    mydatetime = datetime.now()
    mydate = str(mydatetime.date())

    p1Filename = makeFile(panel1,panel1TempDir)
    #p2Filename = makeFile(panel2,mydate,panel2TempDir)
    print('files made, running histogram mode for gain sweep')
    #print(p1Filename)
    #print(p2Filename)
    p1FileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel1TempDir}/histogramRuns'
    #p2FileDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panel2TempDir}/{mydate}/histogramRuns'
    #print(p1FileDir)
    #print(p2FileDir)

    if os.path.isfile(p1Filename):
        with open(p1Filename) as f1:
            inList = f1.readlines()
            #for i in inList:
                #print(i)
            
            nGainRan = len(inList)-1
            startVoltage = int(inList[-1].split(',')[1])
            print(startVoltage, nGainRan)
        
    else:
        startVoltage = 2800
        nGainRan = 0




    for i in range(20-nGainRan):
        voltage = startVoltage - i*5
        print(f'running panels at voltage setting {voltage}\n')
     
        if os.path.isdir(p1FileDir):
            p1dir_list_start = os.listdir(p1FileDir)

        if not os.path.isdir(p1FileDir):
            p1dir_list_start = []

        p1StartFiles=0
   

        for j in p1dir_list_start:
            if str(f'panel{panel1}') in j:
                p1StartFiles+=1


        
        p1 = Process(
        target=hm.main,args=(0,panel1,threshold,voltage,runTime,p1Filename)
        )
        p1.daemon = True
      

        p1.start()
        p1.join()
     
        
        p1dir_list = os.listdir(p1FileDir)
  

        #p1dir_list.sort()
        p1NumFiles=0
       
        for j in p1dir_list:
            if str(f'panel{panel1}') in j:
                p1NumFiles+=1

     
        
        #check if both files written ( files written at end of histogram.main() )
        print(f'panel {panel1} number of files at start {p1StartFiles} number after run try {(p1NumFiles)}')
       
  


def makeFile(panel,tempDir):
    mydatetime = datetime.now()
    mydate = str(mydatetime.date())
    runDir = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{tempDir}/voltageSweeps'
    here = os.path.dirname(os.path.abspath(__file__))
    #print(f'here is {here}')
    if os.path.exists(runDir):
    #if os.path.exists(os.path.join(here, runDir)):
        rateFileName = f'{runDir}/panel{panel}VoltageSweep_{mydate}.txt'
        #print(f'rate file is {rateFileName}')

    else:
        print('directory doesnt exist')
        os.makedirs(runDir)
        #os.makedirs(os.path.join(here, runDir))
        rateFileName = f'{runDir}/panel{panel}VoltageSweep_{mydate}.txt'
        #print(rateFileName)
    
    return rateFileName

if __name__ == "__main__":
    main()