#!/usr/bin/env python3

import subprocess
from subprocess import PIPE, Popen
import os
dataDir = '/home/retcr/deployment/panelSoftware24Season/runs'


mainDir = os.listdir(dataDir)

for n,i in enumerate(mainDir):
    #print(i.strip('\n')[:4])
    if (i.strip(('\n'))[:4] == '2024'):
        newDir = f'{dataDir}/{i}/hitBufferRuns'
        print(f'\t {newDir}')

        if n > 10:
            break
