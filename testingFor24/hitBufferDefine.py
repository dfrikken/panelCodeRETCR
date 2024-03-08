#defining python functions to be used in hit buffer mode
import sys
import os
import math
import argparse
import time
import glob
import serial
import datetime
import json
from cobs import cobs
import subprocess
from subprocess import PIPE, Popen


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

    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True
    )
    process.wait()
    return process.communicate()


def closeSerial(serial):
    serial.flushInput()
    serial.flushOutput()
    serial.close()

def cmdLoop(msg, serial, ntry=15, decode=True):
    for i in range(ntry):
        serial.flushInput()
        serial.flushOutput()
        print(f'{msg} try {i}')
        serial.write((msg+'\n').encode())
        out = collect_output(serial, decode)
        if decode:
            if 'OK' in out:
                return out
            else:
                serial.flushInput()
                serial.flushOutput()
        else:  
            if 'OK' in out[-4:].decode(): #errors="ignore" in decode()
                return out
            else:
                print("looping")
                serial.flushInput()
                serial.flushOutput()
    print('ERROR: giving up')


# A method of collecting the output with an interbyte timeout
def collect_output(serial, decode=True): 		
    slept = False
    if decode:
        out = ''
    else:
        out = bytearray()
        
    while True:
        n = serial.inWaiting()
        if n == 0:
            if not decode:
                if slept == True:
                    break
                time.sleep(0.05)
                slept = not slept
            if decode:
                if slept == True:
                    continue
                slept = not slept
            
        else:
            if decode:
                line = serial.readline()
                if not line: 
                    break
                out += line.decode()
                n = serial.inWaiting()
                #print(line)
                if n!=0:
                    line = serial.read(n)
                    out += line.decode()
                serial.flushInput()
                serial.flushOutput()
                break
            else:
                out.extend(serial.read(n))
            slept = False
    return out



def getNEvents(ser):
    stats = cmdLoop('get_run_statistics', ser).strip().split()
    events = int(stats[1])
    duration = float(stats[4])
    trigrate = events / duration
    return events
    
def getRate(ser):
    stats = cmdLoop('get_run_statistics', ser).strip().split()
    print(stats[1],stats[4])
    events = int(stats[1])
    duration = float(stats[4])
    trigrate = events / duration
    return round(trigrate, 1)

def getNextRun(port, runsdir='runs'):
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, runsdir)):
        lastrun = sorted(glob.glob(os.path.join(here, runsdir, f'port_{port}_run_*')))
        if lastrun:
            lastrun = int(lastrun[-1].split('run_')[-1])
        else:
            lastrun = 0
    else:
        lastrun = 0
    run = 'port_{0}_run_{1}'.format(str(port),str(lastrun+1).zfill(7))
    rdir = os.path.join(here, runsdir, run)
    os.makedirs(os.path.join(here, runsdir, run))
    return rdir, run

# cobs decoding the frames
def cobsDecode(binaryDump, debug=0):

    # find all the frame markers
    markers = []
    for i, val in enumerate(binaryDump):
        bval = val.to_bytes(length=1, byteorder='little')
        if bval == b'\x00':
            markers.append(i)
    if debug: print('COBS: found', len(markers)/2., 'frames')
    
    alldata = bytearray()
    for i in range(0, len(markers), 2):
        
        # grab the frame markers
        fstart = markers[i]
        fstop = markers[i+1]
        
        # select the frame
        cdata = binaryDump[fstart+1:fstop]
        
        # cobs decode the frame
        data = cobs.decode(cdata)
        
        # grab the checksum or later checking - trailing 2 bytes
        #cs = data[-2:]
        #if debug: print(cs)
        
        # skip "number of messages" frame
        if len(data) == 5:
            if debug: print('COBS: skipping message frame --> {0}'.format(data))
            continue
        
        # skip "OK" frame
        if 'OK' in data.decode(errors="ignore"):
            if debug: print('COBS: skipping \"OK\" frame --> {0}'.format(data))
            continue
        
        # strip off the BusID - first 1 byte
        # strip off the checksum - trailing 2 bytes
        alldata.extend(bytearray(data[1:-2]))
        
    return alldata
