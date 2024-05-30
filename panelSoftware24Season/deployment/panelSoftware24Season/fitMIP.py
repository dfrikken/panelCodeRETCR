#!/usr/bin/env python

from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import pylandau
import os

def main():

    hit.testFunction(300)

    panel1 = os.environ['panel1']
    panel2 = os.environ['panel2']

    serNone = serial.Serial()

    panel1Temp = hit.getPanelTemp(panel1,serNone)
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


    '''
    panelNumber = f'panel{panelToRun}'
    panel = os.environ[panelNumber]

    #runDirectory = '/Users/frikken.1/documents/GitHub/panelCodeRETCR/runs/normalizationRuns/station46/2024-05-14/voltageSweeps/histogramRuns/'
    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns'
    dir_list = os.listdir(path)
    #print(dir_list)
    fileList = []
    for i in dir_list:
        if '202' in i:
            #print(i)
            fileList.append(i)

    fileList.sort()

    print(f'using files from {fileList[-1]}')
    myDir = f'{path}/{fileList[-1]}/voltageSweeps/histogramRuns'
    if os.path.isdir(myDir):
        for run in range(1,20):
            print(f'voltage sweep run {run} exist for the closest date')
            runStringP0 = f'{myDir}/panel{panel}_run_{run:07d}/panel{panel}_run_{run:07d}_adc0_hist.dat'
            if os.path.isfile(runStringP0):
                print('file found')
                histData = open(runStringP0)
                histList = histData.readlines()
                yList = []
                xList=[]
                for i in histList:
                    
                    if 'voltage' in i:
                        #print(i.strip('\n').split(' '))
                        voltage = i.split(' ')[3]
                        print(voltage)

                    if 'threshold' in i:
                        #print(i.strip('\n').split(' '))
                        threshold = i.split(' ')[3]
                    if '#' not in i:
                        x = i.split(' ')[0]
                        y = i.split(' ')[1].strip('\n')
                        yList.append(int(x))
                        for j in range(int(y)):
                            xList.append(int(x))
                n, bins, patches = plt.hist(xList,bins=200,histtype='step',range=(700,4000))
                mip = fitLandau(n,bins) 
                print(mip)

            else:
                break

           
            #return mip

    
    '''
    



def fitLandau(n,bins):
    

    # Create fake data with possion error
    mpv, eta, sigma, A = 1500, 100, 300, 1000
    x = bins[:-1]
    y = n
    f = np.random.normal(np.zeros_like(x), np.sqrt(y))
    yerr = np.ones(f.shape)
    yerr[y < 1] = 1
    y += yerr
    param_bounds=([1000,10,10,200],[4000,400,400,3000])
    # Fit with constrains
    coeff, pcov = curve_fit(pylandau.langau, x, y,
                        sigma=yerr,
                        absolute_sigma=True,
                        p0=(mpv, eta, sigma, A),
                        bounds=param_bounds)

    # Plot
    #plt.errorbar(x, y, np.sqrt(pylandau.langau(x, *coeff)), fmt=".")
    #plt.plot(x, pylandau.langau(x, *coeff), "-")
    #plt.show()
    print(coeff)
    return coeff[0]



if __name__ == "__main__":
    main()