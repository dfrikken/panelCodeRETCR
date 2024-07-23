#!/usr/bin/env python3

import subprocess
from subprocess import PIPE, Popen
import os
dataDir = '/home/retcr/deployment/panelSoftware24Season/runs'


mainDir = os.listdir(dataDir)

for n,i in enumerate(mainDir):
    #print(i.strip('\n')[:4])
    if n > 10:
        break
    if (i.strip(('\n'))[:4] == '2024'):
        print(i)
        newDir = f'{dataDir}/{i}/hitBufferRuns'
        #print(f'{newDir}')

        dayDirList = os.listdir(newDir)

        for m, j in enumerate(dayDirList):
            print(j)
            if m > 10:
                break
            runDir = f'{dayDirList}/{j}'
            print(runDir)
            #runDirList = os.listdir(runDir)
            #print(runDirList)
        print('\n')

            
