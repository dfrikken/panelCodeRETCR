#!/usr/bin/env python

#this is the continuous version of hit buffer mode. This mode is called once 
#only need to spend the initialization time once 
#prints out file at the end of the run (1 hour for now)


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

def main():
    
    #scriptStartupTime = time.time()    #test length of time to get run going
    
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--time', dest='runtime', type=int, default=3600,
                    help='data acquisition time in seconds (default is 3600 seconds (1 hour))')
    ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2650,
                    help='voltage setting in daq units (default is 2650)')
    ap.add_argument('-d', '--disc', dest='disc', type=int, default=1510,
                    help='discriminator setting in daq units (default is 1390)')
    ap.add_argument('-p', '--port', dest='PORT', type=str, default=0,
                    help='/dev/ttyUSB port to use (default is 0)')
    ap.add_argument('-m', '--trigRate', dest='TRIGRATE', type=int, default = 10,
                    help='Desired trigger rate to normalize the panels to')
    args = ap.parse_args()
    
    PORT = '/dev/ttyUSB'+ args.PORT

    global activePanel
    activePanel = panelIDCheck(args.PORT)
    file=open(f'output{activePanel}.txt', 'w')
    file.close()
    #find the bias voltage that normalizes gain for array
    biasVoltage = getBiasVoltage(activePanel)

    #set the sub run time to fill the buffer with ~4000 events
    subRunTime = int(3000/args.TRIGRATE)
    #print(subRunTime)
    #subruntime = args.subRunTime

    #check sweep file to get threshold setting for trigger rate
    print(f'Fetching threshold settings for desired trigger rate', file=open(f'output{activePanel}.txt', 'a'))
    discriminatorSetting= getThresholds(args.TRIGRATE, activePanel)
    print(f'Desired trigger rate for panel {activePanel} is {args.TRIGRATE} at thresholds {discriminatorSetting}', file=open(f'output{activePanel}.txt', 'a'))
    
    # voltage sanity check
    if args.voltage > 2800:
        print('ERROR: voltage setting should never need to be >2800')
        sys.exit()
        
    # connect to udaq via USB
    try:
        ser = serial.Serial(port=PORT, baudrate=1000000)
    except:
        print("ERROR: is the USB cable connected?")
        sys.exit()
    
    ser.flushInput()
    ser.flushOutput()
    
    # reset any previous settings on the udaq
    commands = [
        'stop_run',
        'set_livetime_enable 0',
        'reset_schedule',
        'adc_reset_thresholds',
    ]
    
    for msg in commands:
        if cmdLoop(msg, ser, ntry=5) is None:
            sys.exit()
        
    # the uid and temperature
    uid = cmdLoop('get_uid', ser).strip().split()
    uid = ' '.join(uid[:3])
    temp = float(cmdLoop('getmon', ser).strip().split()[1])
    
    
    
    # initialize the adcs, set voltage, threshold, etc.
    commands = [
        #'auxdac 1 {0}'.format(args.voltage),
        'auxdac 1 {0}'.format(biasVoltage),
        'dac 1 {0}'.format(discriminatorSetting),
        
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
            sys.exit()
    cmdLoop('cputrig_width 2',ser)
    cmdLoop('set_cputrig_10mhz_enable 1',ser) #testing on
    cmdLoop('set_cputrig_enable 1',ser) #testing on
    
    cmdLoop('trigout_width 10',ser)
    #trigout_mode 2 is the new trigger mode which produces trigger 
    #while the buffer is read
    cmdLoop('trigout_mode 2', ser)
    numberOfRuns = 0 #track number of runs this file has made
    tempSubRunTime = 0 #used in the top of the hour section, replaces subruntime temporarily
   
    ##### start the contination here
    while True:

        #on first run, take a set to the top of the next hour
        if (numberOfRuns ==0):
            deltaHour = datetime.timedelta(hours=1) 
            timeNow = datetime.datetime.now()
            nextHourStaggered = (timeNow + deltaHour).replace(microsecond=0,second=0,minute=0)
            initialRunTime = (nextHourStaggered - timeNow).seconds #time till next top of hour
            print(f'first run length is {initialRunTime} seconds', file=open(f'output{activePanel}.txt', 'a'))
            if subRunTime > initialRunTime: #if the normal subruntime is longer than remaining time to top of hour
                tempSubRunTime = initialRunTime

            runInfo = {}

            #refill the events json dictionary
            runInfo['subruntime'] = subRunTime
            runInfo['runtime'] = initialRunTime
            runInfo['uid'] = uid
            runInfo['temperature'] = temp
            runInfo['voltage'] = biasVoltage
            runInfo['threshold'] = discriminatorSetting
            start_time = time.time()

            subruns = math.floor(initialRunTime/float(subRunTime))
            if subruns <= 0 : subruns = 1
            runInfo['subruns'] = subruns
            runTimeForLeftover = initialRunTime

        #normal 1 hour runs from top of rPI hour
        elif (numberOfRuns !=0):

            start_time = time.time()

            # dictionary of run info to be json dumped later
            runInfo = {}

            #refill the events json dictionary
            runInfo['subruntime'] = subRunTime
            runInfo['runtime'] = args.runtime
            runInfo['uid'] = uid
            runInfo['temperature'] = temp
            runInfo['voltage'] = biasVoltage
            runInfo['threshold'] = discriminatorSetting

            
            subruns = math.floor(args.runtime/float(subRunTime))
            if subruns <= 0 : subruns = 1
            if (subruns * subRunTime) > args.runtime:
                subruns-=1
            runInfo['subruns'] = subruns
            runTimeForLeftover = args.runtime
        
        #fill json with timestamp from rPI and the uDAQ time for correction later on
        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        mytime = str(mydatetime.time().strftime("%H:%M:%S:%f"))
        
        runInfo['date'] = mydate
        runInfo['time'] = mytime
        runInfo['udaq_time'] = cmdLoop('print_time', ser).split('\n')[0]
        
        # start and stop the run here
        data = []
        cmdLoop('set_livetime_enable 1', ser)
        
        #new trigout mode which forms triggers at all times, whether run active or not
        #needs testing before uncommenting
        #cmdLoop('trigout_mode 2',ser)
        
        out = None
        #print("startup time --- %s seconds ---" % (time.time()- scriptStartupTime)) #print out time to get a run going
        start_time = time.time()
        for i in range(subruns):
            print(f'subrun {i} of {subruns}', file=open(f'output{activePanel}.txt', 'a'))
            if(i < (subruns-1)): #if not last run, do full subrun 

                if tempSubRunTime != 0: 
                    print(f'sleeping for {tempSubRunTime} seconds', file=open(f'output{activePanel}.txt', 'a'))
                    if cmdLoop('run 1 0 0', ser, 5) is None:
                        break
                    time.sleep(tempSubRunTime)
                    tempSubRunTime = 0
                    #break

                else: 
                    print(f'sleeping for {subRunTime} seconds', file=open(f'output{activePanel}.txt', 'a'))
                    if cmdLoop('run 1 0 0', ser, 5) is None:
                        break
                    time.sleep(subRunTime)
                
                # In noisy environments or with really high rates
                # the stop command takes a number of retries before
                # the udaq actually processes the command.
                out = cmdLoop('stop_run', ser, 50)
                
                if out is None:
                    print('problem reading buffer. stopping subrun', file=open(f'output{activePanel}.txt', 'a'))
                    break
                
                #dump the buffer to the data list 
                dump = cmdLoop('dump_hits_binary', ser, ntry=50, decode=False)
                if dump is not None:
                    data.append(dump)
                rate = getRate(ser)
                print(datetime.datetime.now(), file=open(f'output{activePanel}.txt', 'a'))
                print('INFO: trigger rate = {0} Hz'.format(rate), file=open(f'output{activePanel}.txt', 'a'))
                #print(f'number of triggers = {int(rate*subruntime)}', file=open(f'output{activePanel}.txt', 'a'))
                #if rate > 0.0:
                #continue  #skip all the below and just make the next subrun


            else: #on last run, make subrun the remaining time to the top of the hour
                print(f'running final subrun', file=open(f'output{activePanel}.txt', 'a'))
                timeNow = time.time()
                print(start_time, runTimeForLeftover, timeNow)
                endOfRun_subruntime = int((start_time +runTimeForLeftover) - timeNow)
                print(f'end of run subtime is {endOfRun_subruntime}', file=open(f'output{activePanel}.txt', 'a'))
                if cmdLoop('run 1 0 0', ser, 5) is None:
                        break
                if endOfRun_subruntime >0:
                    time.sleep(endOfRun_subruntime)

                out = cmdLoop('stop_run', ser, 50)
                
                if out is None:
                    break
                
                dump = cmdLoop('dump_hits_binary', ser, ntry=50, decode=False)
                if dump is not None:
                    data.append(dump)
        
        if not len(data) > 0:
            print('\nERROR: no data found', file=open(f'output{activePanel}.txt', 'a'))
            #return

        # determine the run number and dir path/name
        rundir, runfile = getNextRun(activePanel)
        
        # write out the binary
        with open(os.path.join(rundir, runfile+'.bin'), 'wb') as bfile:
            for dump in data:
                bfile.write(cobsDecode(dump))
        
        # write the info to json
        with open(os.path.join(rundir, runfile+'.json'), 'w') as jfile:
            json.dump(runInfo, jfile, separators=(', ', ': '), indent=4)

        
        print(f'\n SUCCESS: wrote run {numberOfRuns} data to [{runfile}]\n', file=open(f'output{activePanel}.txt', 'a'))
        numberOfRuns+=1


# cobs decoding the frames
def cobsDecode(binaryDump, debug=0):

    # find all the frame markers
    markers = []
    for i, val in enumerate(binaryDump):
        bval = val.to_bytes(length=1, byteorder='little')
        if bval == b'\x00':
            markers.append(i)
    if debug: print('COBS: found', len(markers)/2., 'frames', file=open(f'output{activePanel}.txt', 'a'))
    
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
            if debug: print('COBS: skipping message frame --> {0}'.format(data), file=open(f'output{activePanel}.txt', 'a'))
            continue
        
        # skip "OK" frame
        if 'OK' in data.decode(errors="ignore"):
            if debug: print('COBS: skipping \"OK\" frame --> {0}'.format(data), file=open(f'output{activePanel}.txt', 'a'))
            continue
        
        # strip off the BusID - first 1 byte
        # strip off the checksum - trailing 2 bytes
        alldata.extend(bytearray(data[1:-2]))
        
    return alldata


# flush and close the serial connection
def closeSerial(serial):
    serial.flushInput()
    serial.flushOutput()
    serial.close()

def getBiasVoltage(activePanel):
    #read the bias voltage file to match sipm gains
    port0BiasFileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{activePanel}SweepBias.txt'
    port0DiffList=[]
    startingTrigRate = 200
    port0SweepList=[]
    port0File = open(port0BiasFileName,'r')

    for line in port0File:
        splitLine = line.strip('\n').split('\t')
        port0SweepList.append([splitLine[0],splitLine[1]])
        #print([splitLine[0],splitLine[1]])

   
    
    for i in range(len(port0SweepList)-1):
        #print(port0SweepList[i][0], port1SweepList[i][0])
        port0DiffList.append(abs(float(startingTrigRate) - float(port0SweepList[i][1])))
        #port1DiffList.append(abs(float(startingTrigRate) - float(port1SweepList[i][1])))
        

    port0MinIndex = port0DiffList.index(min(port0DiffList))
    #port1MinIndex = port1DiffList.index(min(port1DiffList))
    print(f'bias voltage setting is {int(port0SweepList[port0MinIndex][0])}')
    return  int(port0SweepList[port0MinIndex][0])
    

def getThresholds(desiredTriggerRate, activePanel):
    #dumb way to get the closest threshold, but should work

    panelSweepFileName = f'/home/retcr/deployment/stationPIPanelSoftware/hitBufferMode/panel{activePanel}ThresholdSweep.txt'
    

    if not (os.path.isfile(panelSweepFileName)):
        #check if sweep file exists
        print(f'panel {activePanel} threshold file does not exist... run python runHitBufferNormalization.py', file=open(f'output{activePanel}.txt', 'a'))

    if (os.path.isfile(panelSweepFileName)):
       
        print('found threshold sweep files', file=open(f'output{activePanel}.txt', 'a'))
        #open the files and fill lists to use in fine tuner
        port0SweepList = []
        port0File = open(panelSweepFileName,'r')
        for line in port0File:
            splitLine = line.strip('\n').split('\t')
            port0SweepList.append([splitLine[0],splitLine[1]])

    #print(f'length of sweep list is {len(port0SweepList)}')
    port0DiffList=[]
    for i in range(len(port0SweepList)):
        port0DiffList.append(abs(float(desiredTriggerRate) - float(port0SweepList[i][1])))
        
    port0MinIndex = port0DiffList.index(min(port0DiffList))

    return int(port0SweepList[port0MinIndex][0]) 


# try the command ntry times
def cmdLoop(msg, serial, ntry=5, decode=True):
    for i in range(ntry):
        print(msg, file=open(f'output{activePanel}.txt', 'a'))
        serial.write((msg+'\n').encode())
        out = collect_output(serial, decode)
        if decode:
            if 'OK' in out:
                return out
            else:
                print(out)
                serial.flushInput()
                serial.flushOutput()
                time.sleep(0.08)
        else:
            if 'OK' in out[-4:].decode(errors="ignore"):
                #print('in ok section')
                return out
            else:
                serial.flushInput()
                serial.flushOutput()
                #print('im in the flush section')
                time.sleep(0.05)
    print('ERROR: giving up', file=open(f'output{activePanel}.txt', 'a'))
    #closeSerial(serial)
    return None


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
            if slept == True:
                break
            time.sleep(0.05)
            slept = not slept
        else:
            if decode:
                out += serial.read(n).decode()
            else:
                out.extend(serial.read(n))
                time.sleep(0.05)
                #print('im in the extend section')
                #print('out =', bytes(out))
            slept = False
    return out


# set the next run number and output dir
def getNextRun(activePanel, runsdir='runs'):
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, runsdir)):
        lastrun = sorted(glob.glob(os.path.join(here, runsdir, f'panel{activePanel}_run_*')))
        if lastrun:
            lastrun = int(lastrun[-1].split('run_')[-1])
        else:
            lastrun = 0
    else:
        lastrun = 0
    run = 'panel{0}_run_{1}'.format(activePanel,str(lastrun+1).zfill(7))
    rdir = os.path.join(here, runsdir, run)
    os.makedirs(os.path.join(here, runsdir, run))
    return rdir, run

    
def getRate(ser):
    stats = cmdLoop('get_run_statistics', ser, 50).strip().split()
    events = int(stats[1])
    duration = float(stats[4])
    trigrate = events / duration
    return round(trigrate, 1)

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

if __name__ == "__main__":
    main()

