import subprocess
from subprocess import PIPE, Popen
import time


def main():
    #panel id 
    panel3ID = "240045 48535005 20353041" #spare panel at OSU
    panel12ID = "240004 48535005 20353041" #spare panel at OSU
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


    panelList = []
    for n,i in enumerate(panelNumberList):
        tempList = []
        tempList.append(i)
        tempList.append(panelIDList[n])
        panelList.append(tempList)

    activatedPanelList = []
    for portVal in range(2):
        print("startup process for port " + str(portVal)+"\n")

        for i in range(5):   
            #original firmware file
            #outLine = cmdline("stm32flash -b 115200 -w uDAQ-2.0-ultralite-2022-12-05.bin -g 0x0 /dev/ttyUSB" + str(portVal))
            
            #updated firmware with trigger formed outside active runs (no deadtime)
            #needs testing prior to use
            outLine = cmdline("stm32flash -b 115200 -w /home/retcr/deployment/stationPIPanelSoftware/uDAQ-ultralite-20230425.bin -g 0x0 /dev/ttyUSB" + str(portVal))
            
            if 'done' in str(outLine):
                time.sleep(1)
                testCommOutLine2 = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/commTest.py -p " + str(portVal))
                testCommOutLine = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/commTest.py -p " + str(portVal))
                testSplit = str(testCommOutLine[0]).split('\\n')

                for n,panel in enumerate(panelList):
                        if testSplit[1] in panel:
                            print(f"panel {panel[0]} ready for operation"+"\n")
                            activatedPanelList.append(['/dev/ttyUSB'+str(portVal), panel[0]])
                #print('port /dev/ttyUSB'+str(portVal)+ ' execution started, ready to start data collection')
                break
            
            if i == 4:
                #print(portVal)
                #time.sleep(5)
                testCommOutLine = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/commTest.py -p " + str(portVal))
                testCommOutLine2 = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/commTest.py -p " + str(portVal))
                #print("python commTest.py -p " + str(portVal))
                if "OK" in str(testCommOutLine2):
                    testSplit = str(testCommOutLine2[0]).split('\\n')
                    #print(testSplit[1])
                    for n,panel in enumerate(panelList):
                        if testSplit[1] in panel:
                            print(f"panel {panel[0]} ready for operation" +"\n")
                            activatedPanelList.append(['/dev/ttyUSB'+str(portVal), panel[0]])
                    #print("uDAQ " +str(portVal) +" ready for operation")
                else:
                    print("uDAQ not found in port /dev/ttyUSB" +str(portVal)+"\n")


    if len(activatedPanelList) == 2:
        return f'panels {activatedPanelList[0][1]} and {activatedPanelList[1][1]} active'
    
    else:
        return f'problem activating a panel, may need to power cycle. Contact Dylan'

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