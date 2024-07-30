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
import numpy as np
import signal
from threading import Thread
import subprocess
from subprocess import PIPE, Popen

from multiprocessing import Process




def main():
    #hit.testFunction(3000)

    '''
        path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
        here = os.path.dirname(path)
        listTemps = os.listdir(here)

        for temp in listTemps:
            print(f'{temp} \n')
            tempDir = os.path.join(here,temp)
            tempDirList= os.listdir(tempDir)
            print(tempDirList)
            print('\n\n')
    '''

    for tempToTest in range(-23,0):

        panelTemp = float(tempToTest)


        path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
        dir_list = os.listdir(path)
        #print(dir_list)
        fileList = []
        for i in dir_list:
            fileList.append(i)
            bottom = int(i.split('_')[0])
            top = int(i.split('_')[1])
            #print(bottom,top)
            if bottom<=panelTemp <=top:#in range(bottom,top):
                print(i)
                temp = i
                tempRange = i
                print(f'temp dir is {temp}')
                break

        tempDir = os.path.join(path, temp)
        print(tempDir)
        temp_dir_list = os.listdir(tempDir)
        temp_dir_list.sort()


if __name__ == "__main__":
    main()