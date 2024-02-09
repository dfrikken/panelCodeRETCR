#!/usr/bin/env python

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
    
   
    print(f'Starting trigger rate normalization for station histogram mode')

    #port0FileName = f'panel{port0Panel}ThresholdSweep.txt'
    #port1FileName = f'panel{port1Panel}ThresholdSweep.txt'

    #using already made runs for panels 7,14
    #port0FileName = f'panel{port0Panel}ThresholdSweepBias2500.txt'
    #port1FileName = f'panel{port1Panel}ThresholdSweepBias2500.txt'

    #bias voltage sweeps for normalization of threshold sweep curve
    port0FileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{port0Panel}SweepBias.txt'
    port1FileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{port1Panel}SweepBias.txt'

    if not (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check if sweep file exists
        print(f'one of the threshold files does not exist... creating')
        thresholdSweep(port0Panel,port1Panel)
#print(f'Full station trigger rate normalization complete')
        

    if (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check the sweep files for completeness and same length
       
        
        print('found threshold sweep files')
        #open the files and fill lists to use in fine tuner
        port0SweepList = []
        port0File = open(port0FileName,'r')
        for line in port0File:
            splitLine = line.strip('\n').split('\t')
            port0SweepList.append([splitLine[0],splitLine[1]])
            #print([splitLine[0],splitLine[1]])

        port1SweepList = []
        port1File = open(port1FileName,'r')
        for line in port1File:
            splitLine = line.strip('\n').split('\t')
            port1SweepList.append([splitLine[0],splitLine[1]])
            #print([splitLine[0],splitLine[1]])
       
    

        
    desiredRate = args.TRIGRATE
    #print(getThresholds(desiredRate, port0SweepList, port1SweepList))
    if (getThresholds(desiredRate,port0SweepList,port1SweepList)) :
        print(f'Desired rate of {desiredRate}Hz at {getThresholds(desiredRate, port0SweepList, port1SweepList)} discriminator setting')
        print(f'Full station trigger rate normalization complete')

    #return getThresholds(desiredRate, port0SweepList, port1SweepList)


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
    commOutLine = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/commTest.py -p " + str(port))
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
    for i in range(len(port0SweepList)-1):
        #print(float(port0SweepList[i][1]), float(port1SweepList[i][1]))
        port0DiffList.append(abs(float(desiredTriggerRate) - float(port0SweepList[i][1])))
        port1DiffList.append(abs(float(desiredTriggerRate) - float(port1SweepList[i][1])))
        

    port0MinIndex = port0DiffList.index(min(port0DiffList))
    port1MinIndex = port1DiffList.index(min(port1DiffList))
    #print(min(port0DiffList), min(port1DiffList))
    if(min(port0DiffList) < 10. and min(port1DiffList) <10.):
        return [ int(port0SweepList[port0MinIndex][0]), int(port1SweepList[port1MinIndex][0]) ]
    else:
        print(f'desired trig rate of {desiredTriggerRate} not found in threshold sweep')
            


def thresholdSweep(port0Panel,port1Panel):
    #print('Beggining threshold sweep')
    print('begginning bias voltage sweep')
    biasVoltage = 2600
    #port0FileName = f'panel{port0Panel}ThresholdSweepBias{biasVoltage}.txt'
    #port1FileName = f'panel{port1Panel}ThresholdSweepBias{biasVoltage}.txt'
    port0FileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{port0Panel}SweepBias.txt'
    port1FileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{port1Panel}SweepBias.txt'
    port0File = open(port0FileName, "w")
    port1File = open(port1FileName, "w")
    runTime = 10
    threshold = 1450
    

    for i in range(31):
        #threshold+=10
        biasVoltage-=5
        #print(f'Threshold value = {threshold}')
        print(f'bias voltage setting {biasVoltage}')
        runHistString = f'python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/normalizeHitBuffer.py -p 0 -d {threshold} -v {biasVoltage} -t {runTime} -s 10 & python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/normalizeHitBuffer.py -p 1 -d {threshold} -v {biasVoltage} -t {runTime} -s 10 &'
        outLine = cmdline(runHistString)
        outLineString = str(outLine).split('\\n')
        for j in outLineString:
            if(f'Panel {port0Panel} trigger' in j):
                print(f'panel {port0Panel} trigger rate = {float(j.split()[5])}Hz')
                #port0File.write(f'{threshold} \t {float(j.split()[5])}\n')
                port0File.write(f'{biasVoltage} \t {float(j.split()[5])}\n')
                
            if(f'Panel {port1Panel} trigger' in j):
                print(f'panel {port1Panel} trigger rate = {float(j.split()[5])}Hz')
                #port1File.write(f'{threshold} \t {float(j.split()[5])}\n')
                port1File.write(f'{biasVoltage} \t {float(j.split()[5])}\n')
                
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