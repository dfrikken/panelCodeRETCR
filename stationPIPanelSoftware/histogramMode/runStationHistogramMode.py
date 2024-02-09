#!/usr/bin/env python

#usage: python runStationHistogramMode.py -t {desired trigger rate}

#run the station in histogram mode. No individual hit information
#runs for 1 year



import subprocess
from subprocess import PIPE, Popen
import argparse
import os.path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--trigRate', dest='TRIGRATE', type=int, default = 10,
                    help='Desired trigger rate to normalize the panels to')
    args = ap.parse_args()

    port0Panel = panelIDCheck(0)
    port1Panel = panelIDCheck(1)

    #runTime = args.runTime #uncomment for debugging 
    runTime = 31556952 #run for one year

    print(f'Fetching the threshold setting for the desired trigger rate')
    thresholdList = getThresholds(args.TRIGRATE, port0Panel, port1Panel)

    print(f'Running full station histogram mode for {runTime} seconds')
    runHistString = f'python /home/retcr/deployment/stationPIPanelSoftware/histogramMode/histogramMode.py -p 0 -d {thresholdList[0]} -t {runTime} & python histogramMode.py -p 1 -d {thresholdList[1]} -t {runTime} &'
    outLine = cmdline(runHistString)
    
    #uncomment for debugging outputs
    #outLineString = str(outLine).split('\\n')
    #for i in outLineString:
        #if("trigger" in i):
            #print(i)



def getThresholds(desiredTriggerRate, port0Panel, port1Panel):
    
    port0FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port0Panel}ThresholdSweep.txt'
    port1FileName = f'/home/retcr/deployment/stationPIPanelSoftware/histogramMode/panel{port1Panel}ThresholdSweep.txt'
   
    if not (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check if sweep file exists
        print(f'one of the threshold files does not exist... run python normalizeHistogramMode.py')
        
    if (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        
        print('found threshold sweep files')
        
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
    
    port0DiffList=[]
    port1DiffList=[]
    for i in range(len(port0SweepList)):
        port0DiffList.append(abs(float(desiredTriggerRate) - float(port0SweepList[i][1])))
        port1DiffList.append(abs(float(desiredTriggerRate) - float(port1SweepList[i][1])))

    port0MinIndex = port0DiffList.index(min(port0DiffList))
    port1MinIndex = port1DiffList.index(min(port1DiffList))

    return [ int(port0SweepList[port0MinIndex][0]), int(port1SweepList[port1MinIndex][0]) ]
            




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