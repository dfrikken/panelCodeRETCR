#!/usr/bin/env python

#usage: python normalizeHistogramMode.py -t {desired trigger rate (optional)}

#might end up doing this by requiring a set number of events per threshold instead of time based

#normalizes the histogram mode trigger rate of two scintillator panels, call this in the histogram mode script
#the threshold sweep only needs to be ran once

import subprocess
from subprocess import PIPE, Popen
import os.path
import argparse


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--trigRate', dest='TRIGRATE', type=int, default = 10,
                    help='Desired trigger rate to normalize the panels to')
    args = ap.parse_args()


    port0Panel = panelIDCheck(0)
    port1Panel = panelIDCheck(1)
    
    #expand this time in field for a bit more precision in the sweepfile
    runTime = 5
   
    print(f'Starting trigger rate normalization for station histogram mode')

    port0FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port0Panel}ThresholdSweep.txt'
    port1FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port1Panel}ThresholdSweep.txt'
    thresholdSweep(port0Panel,port1Panel)
    if not (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check if sweep file exists
        print(f'one of the threshold files does not exist... creating')
        #thresholdSweep(port0Panel,port1Panel)

    if (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check the sweep files for completeness and same length
        #thresholdSweep(port0Panel,port1Panel)
        '''
        with open(port0FileName, 'r') as fp:
            for countPort0, line in enumerate(fp):
                pass
        fp.close()
        with open(port1FileName, 'r') as fp:
            for countPort1, line in enumerate(fp):
                pass
        fp.close()
        if (countPort0==countPort1==150):
            print('found threshold sweep files')
            #open the files and fill lists to use in fine tuner
            port0SweepList = []
            port0File = open(port0FileName,'r')
            for line in port0File:
                splitLine = line.strip('\n').split('\t')
                port0SweepList.append([splitLine[0],splitLine[1]])

            port1SweepList = []
            port1File = open(port1FileName,'r')
            for line in port1File:
                splitLine = line.strip('\n').split('\t')
                port1SweepList.append([splitLine[0],splitLine[1]])

        elif (countPort0!=countPort1) or countPort0!=150:
            print('problem found with sweep file, recreating')
            thresholdSweep(port0Panel, port1Panel)
    '''

        
    desiredRate = args.TRIGRATE
    #print(f'Desired rate of {desiredRate}Hz at {getThresholds(desiredRate, port0SweepList, port1SweepList)} discriminator setting')
    print(f'Full station trigger rate normalization complete')


def panelIDCheck(port):

    #list panel IDs
    panel3ID = "240045 48535005 20353041"
    panel12ID = "240004 48535005 20353041"  
    panel2ID = "240032 48535005 20353041"
    panel1ID = "24002f 48535005 20353041"
    panel8ID = "21000f 48535005 20353041"
    panel4ID = "210015 48535005 20353041"
    panel11ID = "210007 48535005 20353041"
    panel10ID = "25001a 48535005 20353041"
    panel13ID = "250014 48535005 20353041"
    panel9ID = "210034 48535005 20353041"
    panel6ID = "24003d 48535005 20353041"
    panel5ID = "240012 48535005 20353041"
    panel7ID = "240020 48535005 20353041"
    panel14ID = "260040 48535005 20353041"

    panelIDList = [panel2ID,panel1ID,panel8ID,panel4ID,panel11ID,
                   panel10ID,panel13ID,panel9ID,panel6ID,panel5ID,
                   panel7ID,panel14ID,panel3ID,panel12ID]
    
    panelNumberList=[2,1,8,4,11,10,13,9,6,5,7,14,3,12]

    #comm test to read panelID from result
    commOutLine = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/histogramMode/commTest.py -p " + str(port))
    if "OK" in str(commOutLine):
                commLineSplit = str(commOutLine[0]).split('\\n')
                for n,j in enumerate(panelIDList):
                    if(commLineSplit[1] in j):
                        print(f'panel {panelNumberList[n]} active at port {port}')
                        break

    return panelNumberList[n]



def getThresholds(desiredTriggerRate, port0SweepList, port1SweepList):
    #dumb way to get the closest threshold, but should work

    port0DiffList=[]
    port1DiffList=[]
    for i in range(len(port0SweepList)):
        port0DiffList.append(abs(float(desiredTriggerRate) - float(port0SweepList[i][1])))
        port1DiffList.append(abs(float(desiredTriggerRate) - float(port1SweepList[i][1])))

    port0MinIndex = port0DiffList.index(min(port0DiffList))
    port1MinIndex = port1DiffList.index(min(port1DiffList))

    return [ int(port0SweepList[port0MinIndex][0]), int(port1SweepList[port1MinIndex][0]) ]
            


def thresholdSweep(port0Panel,port1Panel):
    print('Beggining threshold sweep')

    port0FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port0Panel}ThresholdSweep.txt'
    port1FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port1Panel}ThresholdSweep.txt'
    port0File = open(port0FileName, "w")
    port1File = open(port1FileName, "w")
    runTime = 10
    threshold = 1490

    for i in range(250):
        threshold+=10
        print(f'Threshold value = {threshold}')
        runHistString = f'python /home/retcr/deployment/stationPIPanelSoftware/histogramMode/histogramMode.py -p 0 -d {threshold} -t {runTime} & python histogramMode.py -p 1 -d {threshold} -t {runTime} &'
        outLine = cmdline(runHistString)
        outLineString = str(outLine).split('\\n')
        for j in outLineString:
            if("Port 0 trigger" in j):
                print(f'panel {port0Panel} trigger rate = {float(j.split()[5])}Hz')
                port0File.write(f'{threshold} \t {float(j.split()[5])}\n')
            if("Port 1 trigger" in j):
                print(f'panel {port1Panel} trigger rate = {float(j.split()[5])}Hz')
                port1File.write(f'{threshold} \t {float(j.split()[5])}\n')
                
    port0File.close()
    port1File.close()



def cmdline(command):

    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True
    )
    process.wait()
    return process.communicate()

if __name__ == "__main__":
    main()