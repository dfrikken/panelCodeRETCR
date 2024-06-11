#!/usr/bin/env python3

from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import pylandau
import os
import serial
import hitBufferDefine as hit
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--panel', dest='panel', type=str, default=12)
    args = ap.parse_args()

    targetMIP = 1200
    totalMipList = []

    panel = args.panel
    #panel = os.environ['panel1']
    #panel1 = os.environ['panel2']

    serNone = serial.Serial()

    panelTemp = hit.getPanelTemp(panel,serNone)
    #panel2Temp = hit.getPanelTemp(panel2,serNone)
    print(f'temp is {panelTemp}')

    normFilePath = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'

    dir_list = os.listdir(normFilePath)

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
    
    #panel1TempDir = os.path.join(normFilePath, tempDir)
    panelTempDir = tempDir
    print(panelTempDir)

    path = f'/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/{panelTempDir}'
    

    print(f'using files from {path}')

    dir_list = os.listdir(path)


    
    myDir = f'{path}/histogramRuns'
    print(myDir)
    #panel = panel
    mipList = []
    voltList = []

    mipFile = open(f'{path}/panel{panel}_MIPPeaks.txt','w')
    

    
    if os.path.isdir(myDir):
        for run in range(1,50):
            print(f'voltage sweep run {run} exist for the closest date')
            runStringP0 = f'{myDir}/panel{panel}_run_{run:07d}/panel{panel}_run_{run:07d}_adc0_hist.dat'
            if os.path.isfile(runStringP0):
                #print(f'file found {runStringP0}')
                histData = open(runStringP0)
                histList = histData.readlines()
                yList = []
                xList=[]
                for i in histList:
                    
                    if 'voltage' in i:
                        #print(i.strip('\n').split(' '))
                        voltage = i.split(' ')[3].strip('\n')
                        voltList.append(int(voltage))
                        print(voltage)

                    if 'threshold' in i:
                        #print(i.strip('\n').split(' '))
                        threshold = i.split(' ')[3].strip('\n')
                    if '#' not in i:
                        x = i.split(' ')[0]
                        y = i.split(' ')[1].strip('\n')
                        yList.append(int(x))
                        for j in range(int(y)):
                            xList.append(int(x))
                n, bins, patches = plt.hist(xList,bins=200,histtype='step',range=(700,4000))
                mip = fitLandau(n,bins,run,panel,f'{path}') 
                print(mip)
                mipList.append(mip)
                #print(f'{voltage},{threshold},{mip}')
                mipFile.write(f'{voltage},{threshold},{mip}\n')
                

            else:
                break

           
            #return mip
        closeIndex = hit.closest(mipList, targetMIP)
        print(f'MIP target for panel {panel} is {targetMIP}, nearest found {mipList[closeIndex]} with voltage {voltList[closeIndex]}')
        totalMipList.append([panel,mipList[closeIndex],voltList[closeIndex]])
        

    mipFile.close()

    #print(totalMipList)
    return totalMipList

    

    
    
    



def fitLandau(n,bins,run,panel,tempDir):
    

    
    mpv, eta, sigma, A = 1500, 100, 300, 1000
    x = bins[:-1]
    y = n
    f = np.random.normal(np.zeros_like(x), np.sqrt(y))
    yerr = np.ones(f.shape)
    yerr[y < 1] = 1
    y += yerr
    param_bounds=([800,10,10,200],[4000,400,400,3000])
    # Fit with constrains
    coeff, pcov = curve_fit(pylandau.langau, x, y,
                        sigma=yerr,
                        absolute_sigma=True,
                        p0=(mpv, eta, sigma, A),
                        bounds=param_bounds)

    # Plot
    plt.clf()
    plt.errorbar(x, y, np.sqrt(pylandau.langau(x, *coeff)), fmt=".")
    plt.plot(x, pylandau.langau(x, *coeff), "-")
    plt.yscale('log')
    plt.savefig(f'{tempDir}/panel{panel}_run{run}MIP.png')
    plt.show()
    
    #print(coeff)
    return coeff[0]



if __name__ == "__main__":
    main()