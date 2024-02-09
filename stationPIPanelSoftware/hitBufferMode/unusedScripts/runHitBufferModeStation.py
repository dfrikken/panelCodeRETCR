#!/usr/bin/env python

#writing a test file at hitBufferModeContinous.py
    #this file will run the hit buffer mode on a loop
    #writing a file at the prescribed moment by station ID
    #will calculate the subruntime and adjust the last to be ended at the writeout time


#todo: change hitBufferMode.py to write file inside that program and continue on
    #until then this script will have a while true
    #check time to start scripts and read buffer

    #FIX SUBRUNTIME to ensure we end exatcly at 3600 seconds
    #Write a stop and write file function to hitBufferMode.py 
    #fill the buffer to 4000 regardless and cut last subrun short

#this is the script that will run both panels in a station in hit buffer mode

#i do the station time staggering here to avoid deadtime overlap
    #each run lasts one hour, cointaining a TBD number of sub runs
    #there is ~.7 seconds of deadtime to read the buffer following each subrun
    #to ensure we always have at least 5 stations activly triggering, i stagger the time of readout and filewrite
    #the start time for each station is a 2 minutes times station ID added to the top of the hour from the rPI time



import subprocess
from subprocess import PIPE, Popen
import os.path
import argparse
import datetime
import time


def main():

    #set the station number!! if this isn't done, deadtime will overlap
    #stations ID 1-6 
    #################################
    stationNumber = 1
    #################################


    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--trigRate', dest='TRIGRATE', type=int, default = 10,
                    help='Desired trigger rate to normalize the panels to')
    args = ap.parse_args()

    #check which panels are active
    port0Panel = panelIDCheck(0)
    port1Panel = panelIDCheck(1)
    
    #setup total runtime for event files and subruntime
    runTime = 3600 #1 hour in seconds for total run time
    subRunTime = int(4000./args.TRIGRATE) #buffer holds 4000 events safely

    numberOfRuns = 0 #count number of runs elapsed
    print(f'Starting hit-buffer mode for station {stationNumber} cointaining panels {port0Panel} and {port1Panel}')
    print(f'Fetching threshold settings for desired trigger rate')
    discriminatorSettingsList= getThresholds(args.TRIGRATE, port0Panel,port1Panel)
    print(f'Desired trigger rate for station {args.TRIGRATE} at thresholds {discriminatorSettingsList}')

    if numberOfRuns ==0: 
        #staggering of station deadtime will occur on this step
        
        #start station 1 at the top of the hour
        #delay each next station by 2 minutes to allow for writing of files
        #and stagger the deadtime throughout the total runtime

        #simulate this with the subruntime to ensure there is no overlap at any point

        #calculate number of seconds to the next top of hour
        staggerMinutes = (stationNumber -1)*2 
        deltaHour = datetime.timedelta(hours=1) 
        timeNow = datetime.datetime.now()
        nextHourStaggered = (timeNow + deltaHour).replace(microsecond=0,second=0,minute=(staggerMinutes))

        initialRunTime = (nextHourStaggered - timeNow).seconds

        runInitialHitBufferString = f'python hitBufferMode.py -p 0 -d {discriminatorSettingsList[0]} -t {initialRunTime} -s {subRunTime} & python normalizeHitBuffer.py -p 1 -d {discriminatorSettingsList[1]} -t {initialRunTime} -s {subRunTime} &'
        outLine = cmdline(runInitialHitBufferString)
        numberOfRuns+=1
        time.sleep(initialRunTime)

    else:
         while True:
            #check time to run all this, may get rid of printing and extra weight for time if needed
            print(f'Starting run {numberOfRuns} of this series at {datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")}')
            numberOfRuns+=1
            runHitBufferString = f'python hitBufferMode.py -p 0 -d {discriminatorSettingsList[0]} -t {runTime} -s {subRunTime} & python normalizeHitBuffer.py -p 1 -d {discriminatorSettingsList[1]} -t {runTime} -s {subRunTime} &'
            outLine = cmdline(runHitBufferString)
            time.sleep(runTime) #this sleep might not be necessary if i can have one of the hit buffer mode calls not in background and everything works










def getThresholds(desiredTriggerRate, port0Panel, port1Panel):
    #dumb way to get the closest threshold, but should work

    port0FileName = f'panel{port0Panel}ThresholdSweep.txt'
    port1FileName = f'panel{port1Panel}ThresholdSweep.txt'

    if not (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
        #check if sweep file exists
        print(f'one of the threshold files does not exist... run python runHitBufferNormalization.py')

    if (os.path.isfile(port0FileName) and os.path.isfile(port1FileName)):
       
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
    commOutLine = cmdline("python commTest.py -p " + str(port))
    if "OK" in str(commOutLine):
                commLineSplit = str(commOutLine[0]).split('\\n')
                for n,j in enumerate(panelIDList):
                    if(commLineSplit[1] in j):
                        print(f'panel {panelNumberList[n]} active at port {port}')
                        break

    return panelNumberList[n]
    

def cmdline(command):
    #function to allow python to run terminal commands
    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True
    )
    process.wait()
    return process.communicate()

if __name__ == "__main__":
    main()