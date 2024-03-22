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
import numpy as np

global logDir
logDir = "logs/"


'''
to do:
    normalization
        bias voltage 
        threshold
            keep the charge info for testing the gain method

    error checking
        serial timeout flagger 
        check data being written
        run a quick comm test to check for response
            if none powercycle
    
    logger for important steps and information with timestamps
        
    hour cycling for datafile writes
        make version that resets the full thing 
        version that stays up
        which is more stable?
        cut 2 seconds before end of hour

    print uDAQ times to file for buffer reads?
        might not be needed with the better readouts but worth a test
    
    rewrite panelIDCheck and checkUDAQ to not use commTest.py

    gpio monitor usage
        -start/stop gpio monitor output into rundir
        -seperate scheduled and normal triggers
    

'''


'''
function list:

testFunction
    - just used to test importing working correctly
resetUDaq
    - resets the uDAQ parameters to make sure the script starts clean
init
    - initialize the adcs, voltage, threshold, hitbuff parameters, etc.
scheduleTriggers
    - schedule trigger pulses to latch timing with the GPIO monitor
deadTimeAppend
    - print the buffer readout deadtime beggining and end times to file
makeJson
    - handles the json file printing
panelIDCheck
    - checks which panel is in use 
cmdline
    - used to issue terminal commands within the python program
closeSerial
    - flushes serial and closes connection
cmdLoop
    - issue commands to uDAQ, returns output from uDAQ
collect_output
    - collects and decodes(if needed) serial output from uDAQ
    - called in cmdLoop
getNEvents
    - print number of hits in the buffer
getRate
    - get trigger rate in Hz from buffer
getNextRun
    - read the output directory for index to name current file
cobsDecode
    - decode the buffer data from dump to print to .bin file
checkUDAQResponse
    - check the port to see if the uDAQ is responsive
    - will expand to power cycle and error flag 
powerCycle
    -cycle the 24V power and start up both panels
    -restart data aquisition and log the event
errorLogger
    -pass error to run log file
    -log file is in the directory
infoLogger
    -pass information to log file
    -might not use but its here
gpioMon
    - run the c gpio monitor
    - has flag for waiting for process end (if checking number of scheduled triggers)
cmdlineNoWait
    - issue terminal commands but dont wait for process to complete
'''

########## temporary functions
def makeJsonSpoof(subruntime, args, rundir, runfile):
    try:
        # dictionary of run info to be json dumped later
        runInfo = {}
        runInfo['subruntime'] = subruntime
        runInfo['runtime'] = args.runtime
        # the uid and temperature
        #uid = cmdLoop('get_uid', ser).strip().split()
        #print(f'uid is {uid}')
        #uid = ' '.join(uid[:3])
        #temp = float(cmdLoop('getmon', ser).strip().split()[1])
        #runInfo['uid'] = uid
        #runInfo['temperature'] = temp
        runInfo['voltage'] = args.voltage
        runInfo['threshold'] = args.disc
        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        runInfo['date'] = mydate
        #subruns = int(round(args.runtime/float(subruntime), 0))
        #if subruns <= 0 : subruns = 1
        #runInfo['subruns'] = subruns
        #runInfo['runTimes'] = []
        #runInfo['udaqTimeSubRuns'] = []
        #runInfo['udaq_time'] = cmdLoop('print_time', ser).split('\n')[0]
        mytime = time.time_ns() #time.clock_gettime_ns(time.CLOCK_REALTIME) #
        runInfo['time'] = mytime
    
        with open(os.path.join(rundir, runfile+'.json'), 'w') as jfile:
            json.dump(runInfo, jfile, separators=(', ', ': '), indent=4)
    except:
        print('json creation error')
        #print(rundir)
        errorLogger('error creating json file')

def testFunction():
   
    print('the definition file imported succesfully')
    
#############


def resetUDaq(ser): #error log entry made
     # reset any previous settings on the udaq
    commands = [
        'stop_run',
        'set_livetime_enable 0',
        'reset_schedule',
        'adc_reset_thresholds',
    ]
    
    for msg in commands:
        if cmdLoop(msg, ser, ntry=5) is None:
            errorLogger('error reseting uDAQ, may be unresponsive')
            sys.exit()

def init(args): #error log entry made
    # initialize the adcs, set voltage, threshold, etc.
    commands = [
        'auxdac 1 {0}'.format(args.voltage),
        'dac 1 {0}'.format(args.disc),
        
        'timestamp_mode 4',
        'disc_opm 1',
        
        
        'adc_timer_delay 0 18',
        'adc_timer_delay 1 136',
        'adc_timer_delay 2 18',
        'adc_timer_delay 3 136',
        'adc_timer_delay 4 18',
        #'adc_timer_delay 4 136',
        'adc_timer_delay 5 136',
        'adc_timer_delay 6 136',
        'adc_timer_delay 7 136',
        
        'adc_hist_enable 0',  # turn off ascii histograms
        
        'adc_recording_thresholds  0 0 0',  # high gain
        'adc_recording_thresholds  2 0 0',  # med gain
        'adc_recording_thresholds 12 0 0',  # low gain
        
        'adc_enable  0 1',  # high gain
        'adc_enable  2 1',  # med gain
        'adc_enable 12 1',  # low gain
        
    ]
    
    for msg in commands:
        if cmdLoop(msg, ser) is None:
            errorLogger('error initializing uDAQ, may be unresponsive')
            sys.exit()

def scheduleTriggers(ser,pin,rundir,seconds=10): #error log entry made
    resetUDaq(ser)
    apFake = argparse.ArgumentParser()
    apFake.add_argument('-v', '--voltage', dest='voltage', type=int, default=0,
                    help='voltage setting in daq units (default is 2650)')
    apFake.add_argument('-d', '--disc', dest='disc', type=int, default=3900,
                    help='discriminator setting in daq units (default is 1390)')
    argsFake = apFake.parse_args()

    print(argsFake)

    cmdLoop('set_livetime_enable 1', ser)
    udaqTime = cmdLoop('print_time', ser).split('\n')[0]
    microTime = udaqTime.split(" ")
    print(f'udaq time is {udaqTime}')
    print(f' edit time = {microTime[1]}')
    for i in range(1,3):
        cmdLoop(f'schedule_trigout_pulse {microTime[0]} {int(microTime[1])+i} {microTime[2]}',ser,5)
        cmdLoop(f'schedule_trigout_pulse {microTime[0]} {int(microTime[1])+i} {int(microTime[2])+100}',ser,5)
        cmdLoop(f'schedule_trigout_pulse {microTime[0]} {int(microTime[1])+i} {int(microTime[2])+500}',ser,5)

    gpioOut = gpioMon(pin,5,rundir)
    gpioFile = str(gpioOut[0]).split('\\n')[1].split(" ")[2]
    gpio = open(gpioFile,'r')
    print(f'{len(gpio.readlines())} scheduled triggers captured')
    if (len(gpio.readlines()) == 0):
        print('no scheduled triggers captured')
        errorLogger('no scheduled triggers captured')
    gpio.close()
    
def deadTimeAppend(beginTime, endTime,rundir): #error log entry made
    try:
        f = open(f"{rundir}/bufferReadout.txt", "a")
        f.write(f'{beginTime},{endTime}\n')
    except:
        errorLogger('error writing dead time')
    #print(f'sub run n at {beginTime}  {endTime}')
    #print(f'buffer readout was {(endTime - beginTime)/1e9} seconds')

def makeJson(subruntime, args, rundir, runfile): #error log entry made
    try:
        # dictionary of run info to be json dumped later
        runInfo = {}
        runInfo['subruntime'] = subruntime
        runInfo['runtime'] = args.runtime
        # the uid and temperature
        uid = cmdLoop('get_uid', ser).strip().split()
        #print(f'uid is {uid}')
        uid = ' '.join(uid[:3])
        temp = float(cmdLoop('getmon', ser).strip().split()[1])
        runInfo['uid'] = uid
        runInfo['temperature'] = temp
        runInfo['voltage'] = args.voltage
        runInfo['threshold'] = args.disc
        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        runInfo['date'] = mydate
        #subruns = int(round(args.runtime/float(subruntime), 0))
        #if subruns <= 0 : subruns = 1
        #runInfo['subruns'] = subruns
        runInfo['runTimes'] = []
        runInfo['udaqTimeSubRuns'] = []
        runInfo['udaq_time'] = cmdLoop('print_time', ser).split('\n')[0]
        mytime = time.time_ns() #time.clock_gettime_ns(time.CLOCK_REALTIME) #
        runInfo['time'] = mytime

        with open(os.path.join(rundir, runfile+'.json'), 'w') as jfile:
            json.dump(runInfo, jfile, separators=(', ', ': '), indent=4)
    
    except:
        errorLogger('error writing json file')

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

def cmdLoop(msg, serial, ntry=15, decode=True): #error log entry made
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
                #print("looping")
                serial.flushInput()
                serial.flushOutput()
    print('ERROR: giving up')
    errorLogger('error in serial comms with uDAQ, checking for response')
    #checkUDAQResponse(serial)

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

def getNEvents(ser): #error log entry made
    try:
        stats = cmdLoop('get_run_statistics', ser).strip().split()
        events = int(stats[1])
        duration = float(stats[4])
        trigrate = events / duration
        return events
    except:
        errorLogger('error getting number events in buffer')
    
def getRate(ser): #error log entry made
    try:
        stats = cmdLoop('get_run_statistics', ser).strip().split()
        print(stats[1],stats[4])
        events = int(stats[1])
        duration = float(stats[4])
        trigrate = events / duration
        return round(trigrate, 1)
    except:
        errorLogger('error getting trigger rate in buffer')

def getNextRun(panel, runsdir='runs'): #error log entry made
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(here, runsdir)):
            lastrun = sorted(glob.glob(os.path.join(here, runsdir, f'panel_{panel}_run_*')))
            if lastrun:
                lastrun = int(lastrun[-1].split('run_')[-1])
            else:
                lastrun = 0
        else:
            lastrun = 0
        run = 'panel_{0}_run_{1}'.format(str(panel),str(lastrun+1).zfill(7))
        rdir = os.path.join(here, runsdir, run)
        os.makedirs(os.path.join(here, runsdir, run))   
        return rdir, run
    except:
        errorLogger('error creating next run directory')

def cobsDecode(binaryDump, debug=0):
    # cobs decoding the frames

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

def checkUDAQResponse(serial,port): #error log entry made
    serial.flushInput()
    serial.flushOutput()

    commOutLine = cmdline("python /home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/commTest.py -p " + str(port))
    if "OK" in str(commOutLine):
                commLineSplit = str(commOutLine[0]).split('\\n')
                for n,j in enumerate(panelIDList):
                    if(commLineSplit[1] in j):
                        print(f'panel {panelNumberList[n]} active at port {port}')
                        break
    else:
        print(f'error in port {port}, panel non-responsive, may need power cycle')

def powerCycle(port):
    #placeholder for now to be filled in later
    #cycle 24V power
    #newPanelStart 
    #restart both panels' data scripts
    print("power cycling the 24V and restarting panels ")

def errorLogger(message):
    errFile = open(logDir+"errorLog.txt","a")
    errFile.write(str(time.time_ns()) + ',' + message+'\n')
    errFile.close()
    #placeholder for error logging
    print("\n*****************")
    print(f'\nerror logged\n\n\t{message}\n')
    print("*****************\n")

def infoLogger():
    #placeholder may not use 
    print('info logged')

def gpioMon(pin, seconds,rundir, wait = 1):
    print(f'\ngpio monitor for pin {pin}')
    print(f'running for {seconds} seconds')
    if 1==wait:
        out = cmdline(f'./testGPIO {pin} {seconds} {rundir}')
        return out
    
    if 0 == wait:
        out = cmdlineNoWait(f'./testGPIO {pin} {seconds} {rundir}')
        return 0

def cmdlineNoWait(command):

    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True
    )
    #process.wait()
    #return process.communicate()