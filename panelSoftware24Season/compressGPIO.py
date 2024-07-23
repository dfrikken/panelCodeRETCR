#!/usr/bin/env python3

import subprocess
from subprocess import PIPE, Popen
import os
dataDir = '/home/retcr/deployment/panelSoftware24Season/runs'


mainDir = os.listdir(dataDir)
gpioCounter=0
fileName = '/home/retcr/deployment/panelSoftware24Season/runs/2024-05-19/hitBufferRuns/panel_1_run_0000023/gpioMon.txt'
#command = f'gzip {runDir}/gpioMon.txt'
command = f'gzip {fileName}'
print(command)
gpioThread = Popen(
    args=command,
    shell = True,
    stdout=subprocess.PIPE,
    preexec_fn=os.setsid
    
)
gpioThread.wait()
gpioThread.terminate() 

'''
for n,i in enumerate(mainDir):
    #print(i.strip('\n')[:4])
    #if n > 2:
    #    break
    if (i.strip(('\n'))[:4] == '2024'):
        print(i)
        newDir = f'{dataDir}/{i}/hitBufferRuns'
        #print(f'{newDir}')

        dayDirList = os.listdir(newDir)

        for m, j in enumerate(dayDirList):
            #print(j)
            #if m > 2:
            #    break
            runDir = f'{newDir}/{j}'
            #print(runDir)
            runDirList = os.listdir(runDir)
            #print(runDirList)
            if 'gpioMon.txt' in runDirList:
                #print('gpio file found')
                gpioCounter+=1
                
                gpioThread = Popen(
                    args=command,
                    shell = False,
                    stdout=subprocess.PIPE,
                    preexec_fn=os.setsid
                    
                )
                gpioThread.wait()
                gpioThread.terminate()                
                
                command = f'gzip {runDir}/gpiomon.txt'
                print(command)
        
                
        print(f'{i} finished \n')
        

print(f'gpio monitor files found {gpioCounter}')
'''


            
