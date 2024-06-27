#!/usr/bin/env python

import os

#import test for fitMIP
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import pylandau
import os
import serial
import hitBufferDefine as hit
import argparse

'''
temp = -27
normFilePath = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'

dir_list = os.listdir(normFilePath)

fileList = []
for i in dir_list:
    fileList.append(i)
    if '202' not in i:
        bottom = int(i.split('_')[0])
        top = int(i.split('_')[1])
        if temp in range(bottom,top):
            #print(i)
            tempDir = i
            tempRange = i
            break

tempDir = os.path.join(normFilePath, tempDir)

print(tempDir)

'''
path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
here = os.path.dirname(path)
print(here)
for i in range(-40,25):
    if i%3 ==0:
        print(f'{i}_{i+2}')
        dirName = f'{i}_{i+2}'
        test = os.path.join(here, dirName)
        print(test)
        os.makedirs(os.path.join(here, dirName))

