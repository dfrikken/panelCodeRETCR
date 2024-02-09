#!/usr/bin/env python


#this is the script that will run both panels in a station in continuous hit buffer mode

import subprocess
from subprocess import PIPE, Popen
import os.path
import argparse
import datetime
import time


def main():

    

    #start the panels up for when this script is in crontab.
    #crontab doesnt order operations correctly so this makes sure panels start prior to data
    #commented until i add the crontab process
    runPanelStartup = f'python /home/retcr/deployment/stationPIPanelSoftware/PanelStartup.py'
    outLinePanelStartup = cmdline(runPanelStartup)

    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--trigRate', dest='TRIGRATE', type=int, default = 10,
                    help='Desired trigger rate to normalize the panels to')
    args = ap.parse_args()

    #check which panels are active
    port0Panel = panelIDCheck(0)
    port1Panel = panelIDCheck(1)
    
    #setup total runtime for event files and subruntime
    runTime = 3600 #1 hour in seconds for total run time
    
    print(f'Station starting continuous hit buffer mode on panels {port0Panel,port1Panel} with trigger rate of {args.TRIGRATE}')
    runHitBufferString = f'python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/hitBufferModeContinuousNewFirmware.py -p 0 -t {runTime} -m {args.TRIGRATE} & python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/hitBufferModeContinuousNewFirmware.py -p 1 -t {runTime} -m {args.TRIGRATE} &'
    outLine = cmdline(runHitBufferString)






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