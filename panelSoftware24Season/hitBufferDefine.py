#defining python functions to be used in hit buffer mode
import sys
import os
import math
import argparse
import time
import glob
import serial
import datetime
from datetime import timedelta
import json
from cobs import cobs
import subprocess
from subprocess import PIPE, Popen
import numpy as np
import signal


global logDir
logDir = "logs/"
#global serialPort

'''
to do:

    normalization
        temperature in 5 degrees C 
            if outside redo a bias and threshold sweep?
            would incur some dead time once per time in that temp range
        
        bias voltage 

        threshold
            keep the charge info for testing the gain method

    error checking
        serial timeout flagger 
        check data being written
        run a quick comm test to check for response
            if none powercycle
    
    DONE -logger for important steps and information with timestamps

    check difference between gpiomon scheduled trigs accuracy per run vs per power cycle
        - use coincident events to check

    gpio monitor 
        done -seperate scheduled and normal triggers
        look into cleaning the signal with a resister and checking accuracy of buffer to gpio monitor
    
'''


'''
function list:

testFunction
    - ensure the library has imported correctly and set the alarm for 2 subrun times
handler
    - handler for the alarm to log error and exit so the main script can restart if needed
changeGlobal
    - allows the controlling program to change the log directory
    - also imports the subruntime as global
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
gpioMon
    - run the c gpio monitor
cmdlineNoWait
    - issue terminal commands but dont wait for process to complete
panelStartup
    - start the panels for operation after power cycling   
powerCycle
    - cycle the 24V power to reset the uDAQ
closest
    - gets closest value in list
    - used in the get threshold and voltage function
getThresholdAndVoltage
    - given a desired trigger rate for a panel, get the settings needed
kelvinToCelcius
    - convert K to C
getPanelTemp
    - get the panel temp for threshold sweep saving
'''


def testFunction(subrunTime=60):
    global srTime
    srTime = subrunTime
    print('the definition file imported succesfully')
    print(f'subrunTime for this run is {srTime}')
    
def handler(signum, frame):
    print('timeout handler')
    errorLogger('error: timeout handler met')
    
    #upFlag = checkUDAQResponse(serialPort)
    #print(f'upflag is {upFlag}')
    sys.exit()
    #raise Exception('Action took too much time')
    
def changeGlobals(newLogDir,ser):
    global serialPort
    serialPort = ser
    global logDir
    logDir = newLogDir
    
    if newLogDir != 'empty':
        print(f'log directory changed to {logDir}')
        
        if not os.path.isdir(logDir):
            print('directory does not exist, creating')
            cmdline(f'mkdir {logDir}')
    return logDir

def resetUDaq(ser): #error log entry made

    print('\nreseting the uDAQ settings')
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

    print("uDAQ reset\n")

def init(ser,args): #error log entry made
    resetUDaq(ser)
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
        
        'adc_recording_thresholds 0 0 0',  # high gain
        'adc_recording_thresholds 2 0 0',  # med gain
        'adc_recording_thresholds 12 0 0',  # low gain
        
        'adc_enable  0 1',  # high gain
        'adc_enable  2 1',  # med gain
        'adc_enable 12 1',  # low gain
        
    ]
    
    for msg in commands:
        if cmdLoop(msg, ser) is None:
            errorLogger('error initializing uDAQ, may be unresponsive')
            sys.exit()

def scheduleTriggers(ser,pin,rundir,seconds=2): #error log entry made
    scheduledTriggerFile = open(rundir+"/scheduledTriggers.txt","a")
    apFake = argparse.ArgumentParser()
    apFake.add_argument('-v', '--voltage', dest='voltage', type=int, default=0,
                    help='voltage setting in daq units (default is 2650)')
    apFake.add_argument('-d', '--disc', dest='disc', type=int, default=3900,
                    help='discriminator setting in daq units (default is 1390)')
    apFake.add_argument('-p','--port',dest="PORT",type=int,default=0)
    argsFake = apFake.parse_args()

    
    init(ser,argsFake)

    
    cmdLoop('set_livetime_enable 1', ser)
    udaqTime = cmdLoop('print_time', ser).split('\n')[0]

    microTime = udaqTime.split(" ")
    numTriggers = 0

    splitTime = udaqTime.split(' ')

    timeVal = splitTime[1] +'.'+ splitTime[2]
    addTime = np.float64(timeVal)
    addTime = np.float64(addTime)+1
    for i in range(10):

        timeToNextTrigger = (10+i)/1000
        #print(timeToNextTrigger)
        addTime = np.float64(addTime)+timeToNextTrigger
        addString = f"{0} {str(addTime.round(6)).split('.')[0]} {str(addTime.round(6)).split('.')[1]}"
        #print(addString)
        cmdLoop(f'schedule_trigout_pulse {addString}',ser,5)
        scheduledTriggerFile.write(f'{addString}\n')
        numTriggers+=1
    
    scheduledTriggerFile.close()
    
    return numTriggers
    
def deadTimeAppend(beginTime, endTime,rundir): #error log entry made
    try:
        f = open(f"{rundir}/bufferReadout.txt", "a")
        f.write(f'{beginTime},{endTime}\n')
        f.close()
    except:
        errorLogger('error writing dead time')
    #print(f'sub run n at {beginTime}  {endTime}')
    #print(f'buffer readout was {(endTime - beginTime)/1e9} seconds')

def makeJson(ser,subruntime, args, rundir, runfile): #error log entry made
    try:
        # dictionary of run info to be json dumped later
        runInfo = {}
        runInfo['subruntime'] = subruntime
        #runInfo['runtime'] = args.runtime
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
        #dont need subrun info if im storing the buffer readout time
        #subruns = int(round(args.runtime/float(subruntime), 0))
        #if subruns <= 0 : subruns = 1
        #runInfo['subruns'] = subruns
        runInfo['udaq_time'] = cmdLoop('print_time', ser).split('\n')[0]
        mytime = time.time_ns() #time.clock_gettime_ns(time.CLOCK_REALTIME) #
        runInfo['time'] = mytime

        with open(os.path.join(rundir, runfile+'.json'), 'w') as jfile:
            json.dump(runInfo, jfile, separators=(', ', ': '), indent=4)
    
    except:
        errorLogger('error writing json file')

def panelIDCheck(ser):

    #list panel IDs
    panel3ID = "240045 48535005 20353041" #osu lab panel
    panel12ID = "240004 48535005 20353041"  #osu lab panel
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

    uid = cmdLoop('get_uid', ser).strip().split()
    #print(f'uid is {uid}')
    uid = ' '.join(uid[:3])
    #print(f'after join uid is {uid} type {type(uid)}')
    for n,j in enumerate(panelIDList):
        if(uid == j):
            print(f'panel {panelNumberList[n]} active')
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

def closeSerial(serialPort):

    cmdLoop('trigout_mode 1',serialPort)
    cmdLoop('stop_run', serialPort, 100)
    cmdLoop('set_livetime_enable 0', serialPort)

    # paranoid safety measure - set voltage back to 0
    cmdLoop('auxdac 1 0', serialPort)
    cmdLoop('auxdac 1 0', serialPort)
    print('im closing the serial port now')

    serialPort.close()
    print("serial connection closed")

    return 0

def cmdLoop(msg, serial, ntry=15, decode=True): #error log entry made
    for i in range(ntry):
        serial.flushInput()
        serial.flushOutput()
        #print(f'{msg} try {i}')
        infoLogger(f'{msg} try {i}')
        serial.write((msg+'\n').encode())
        #start = time.time()
        out = collect_output(serial, decode)
        #print('It took', time.time()-start, 'seconds.')
        
        if decode:
            if 'OK' in out:

                return out
            else:
                #print('in the flush section')
                #print(out)
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
    errorLogger('error in serial comms with uDAQ')
    sys.exit()
    #checkUDAQResponse(serial)

def collect_output(serial, decode=True): 
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(30) #Set the parameter to the amount of seconds you want to wait

    startTime = datetime.datetime.now()
    
    

    slept = False
    if decode:
        out = ''
        endTime = startTime + timedelta(seconds=.1)
    else:
        out = bytearray()
        endTime = startTime + timedelta(seconds=1)
    nTimes = 0
    while datetime.datetime.now() < endTime:
        n = serial.inWaiting()
        if n == 0:
            if not decode:
                if slept == True:
                    break
                time.sleep(0.05)
                slept = not slept
            if decode:
                if slept == True:
                    #print(slept)
                    #if( nTimes > 10):
                        #break
                    #print('here')
                    #serial.flushInput()
                    #serial.flushOutput()
                    #print('flushing')
                    #break
                    continue
                slept = not slept
                #print(slept)
                
            
        else:
            if decode:
                n = serial.inWaiting()
                #print(n)
                if n!=0:
                    line = serial.read(n)
                    
                    
                if not line: 
                    #print('in not line')
                    break
                out += line.decode()
                #print(out)
                n = serial.inWaiting()
                if n!=0:
                    line = serial.read(n)
                    out += line.decode()
                    print('extending')
                break
            else:
                out.extend(serial.read(n))
            slept = False
    #reset alarm for two subruns in case of hangups elsewhere
    signal.alarm(srTime*2) 
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
        
        events = int(stats[1])
        duration = float(stats[4])
        trigrate = events / duration
        print(f'\nrate is {round(trigrate, 1)} Hz over {duration} seconds {events} in buffer\n')
        return round(trigrate, 1)
    except:
        errorLogger('error getting trigger rate in buffer')

def getNextRun(panel, runsdir='runs'): #error log entry made
    try:
        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        runsdir = f'runs/{mydate}/hitBufferRuns'
        print(f'run directory is {runsdir}')
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

def checkUDAQResponse(serial): #error log entry made
    serial.flushInput()
    serial.flushOutput()
   
    panel = panelIDCheck(serial)
    if panel:
        print('panels responsive continuing')
        return 1
    else:
        print(f'error in panel, panel non-responsive, may need power cycle')
        return 0

def errorLogger(message):
    errFile = open(logDir+"errorLog.txt","a")
    errFile.write(str(time.time_ns()) + ',' + message+'\n')
    errFile.close()
    #placeholder for error logging
    print("\n*****************")
    print(f'\nerror logged\n\n\t{message}\n')
    print("*****************\n")

def infoLogger(message):
    #print(f'logdir is {logDir}')
    infoFile = open(logDir+"/infoLog.txt","a")
    infoFile.write(message+'\n')
    infoFile.close()
    
def gpioMon(pin, seconds,rundir, wait = 1, numTriggersExpect = 0,fullRun = 0):
    print(f'\ngpio monitor for pin {pin}')
    print(f'running for {seconds} seconds')
    if 1==wait:
        print('dont use, depricated')
        #out = cmdline(f'./testGPIO {pin} {seconds} {rundir}')
        #return out
    
    if 0 == wait:
        out = cmdlineNoWait(f'./gpioMon {pin} {rundir}',seconds)
        print(f'gpio mon pid is {out.pid}')
        
        print(f'gpio monitor of scheduled triggers complete, checking number of triggers registered\n')
        gpioFile = f'{rundir}/gpioMon.txt'
  
        with open(gpioFile, "rbU") as f:
            numberOfLines = sum(1 for _ in f)
        
        if fullRun == 0:
            numInFile = 0
            with open(gpioFile,'r') as f:
                for line in f:
                    if 'scheduled' in line:
                        break
   
                    if len(line) > 1:
                        numInFile+=1
            print(f'{numInFile} of {numTriggersExpect} scheduled triggers captured')
            infoLogger(f'{numInFile} of {numTriggersExpect} scheduled triggers captured')
            if (numInFile != numTriggersExpect):
                print('problem capturing triggers')
                errorLogger(f'error: problem capturing triggers ({numInFile} of {numTriggersExpect} scheduled triggers captured)')
                return numInFile
            return numInFile

        if fullRun ==1:
            print(f'\n\n{numberOfLines - (numTriggersExpect+2)} entries in gpio monitor full run section\n\n')
        
            return 1

def cmdlineNoWait(command,waitTime ):

    process = Popen(
        args=command,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid
    )
 
    time.sleep(waitTime)
    os.killpg(os.getpgid(process.pid), signal.SIGINT)

    process.terminate()
    process.wait()

    return process

def panelStartup():
    panelUp = 0
    for panel in range(2):
        #print("stm32flash -g 0x0 /dev/ttyUSB" + str(panel))
        for t in range(5):
            #print("stm32flash -g 0x0 /dev/ttyUSB" + str(panel))
            outLine = cmdline("stm32flash -g 0x0 /dev/ttyUSB" + str(panel))
            time.sleep(.3)
            #print(outLine)

            if 'done' in str(outLine):
                print("done")
                panelUp+=1
                break
    if panelUp ==2:
        print('both panels active')
        return 1

def powerCycle():
    # gpio pin 2 controls the 24V power
    import RPi.GPIO as gpio

    gpio.setmode(gpio.BCM)
    gpio.setup(2, gpio.OUT)

    print("high = off")
    gpio.output(2, gpio.HIGH)

    time.sleep(.1)

    print("low = on")
    gpio.output(2, gpio.LOW)
    time.sleep(.5)

def closest(list, Number):
    aux = []
    for valor in list:
        aux.append(abs(Number-valor))

    return aux.index(min(aux))

def getThresholdAndVoltage(panel, trigRate):
    
    print(f'pulling threshold and voltage settings for panel {panel}')
    #temp = float(cmdLoop('getmon', serialPort).strip().split()[1])
    #print(f'temperature is {kelvinToCelcius(temp)} celcius')
    path = '/home/retcr/deployment/panelSoftware24Season/runs/normalizationRuns/'
    dir_list = os.listdir(path)
    #print(dir_list)
    fileList = []
    for i in dir_list:
        if '202' in i:
            #print(i)
            fileList.append(i)

    fileList.sort()
    myFile = f'{path}/{fileList[-1]}/thresholdSweeps/panel{panel}ThresholdSweep_{fileList[-1]}.txt'
    #print(myFile)
    with open(myFile, 'r') as f:
        settingsList = []
        settingsList = f.readlines()

    rateList = []
    for n,j in enumerate(settingsList):
        split = j.split(',')
        if n > 1:
            
            rateList.append(float(split[2]))
    
    #print(rateList)
    myIndex = closest(rateList,trigRate)
    print(f"nearest trigger rate to {trigRate} is {rateList[myIndex]} at voltage {settingsList[myIndex+2].split(',')[0]} threshold {settingsList[myIndex+2].split(',')[1]}")
    #print(rateList[myIndex], settingsList[myIndex+2].split(',')[0],settingsList[myIndex+2].split(',')[1], settingsList[myIndex+2].split(',')[3])
    return [int(settingsList[myIndex+2].split(',')[1]),int(settingsList[myIndex+2].split(',')[0])]
    

def kelvinToCelcius(kelvin):
    celcius = kelvin - 273.15
    return round(celcius,0)

def getPanelTemp(panelToRun):
    id12 = 'usb-FTDI_TTL-234X-3V3_FT76I7QF-if00-port0'
    id3 = 'usb-FTDI_TTL-234X-3V3_FT76S0N6-if00-port0'
    if panelToRun ==12:
        PORT = '/dev/serial/by-id/'+ id12

    if panelToRun ==3:
        PORT = '/dev/serial/by-id/'+ id3

    try:
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE, timeout=3,stopbits=1)
        ser.flushInput()
        ser.flushOutput()
    except:
        print("ERROR: is the USB cable connected?")
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing

    temp = float(cmdLoop('getmon', ser).strip().split()[1])
    ser.close()
    return kelvinToCelcius(temp)

'''
def getPanelSerialID(panel):

    arr = os.listdir('/dev/serial/by-id/')
    id1 = arr[0]
    id2 = arr[1]
    PORT = '/dev/serial/by-id/'+ id1
    #print(PORT)
	# connect to udaq via USB
    ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE,timeout=3,stopbits=1)
    
    panel1 = panelIDCheck(ser)
    
   
    ser.close()
    time.sleep(.5)
    PORT = '/dev/serial/by-id/'+ id2
    
        # connect to udaq via USB

    ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE,timeout=3,stopbits=1)
    
    panel2 = panelIDCheck(ser)
    ser.close()
    time.sleep(.5)
   

    if int(panel) == panel1:
        return id1
    elif int(panel) == panel2:
        return id2
    else:


        errmess = 'panel not found'
        return errmess
'''
