#!/usr/bin/env python

import sys
import os
import argparse
import time
import glob
import serial
import datetime
import json
from cobs import cobs

# the usb device
#PORT = '/dev/ttyUSB0'

# subrun duration in seconds
subruntime = 30


def main():
        
    # dictionary of run info to be json dumped later
    runInfo = {}
    
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--time', dest='runtime', type=int, default=3,
                    help='data acquisition time in seconds (default is 10 seconds)')
    ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2600,
                    help='voltage setting in daq units (default is 2650)')
    ap.add_argument('-d', '--disc', dest='disc', type=int, default=1510,
                    help='discriminator setting in daq units (default is 1390)')
    ap.add_argument('-p','--port',dest="PORT",type=int,default=0)
    args = ap.parse_args()
    PORT = '/dev/ttyUSB' + str(args.PORT)
    runInfo['subruntime'] = subruntime
    runInfo['runtime'] = args.runtime
    
    # voltage sanity check
    if args.voltage > 2800:
        print('ERROR: voltage setting should never need to be >2800')
        sys.exit()
        
    # connect to udaq via USB
    try:
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN)
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
    #print(type(cmdLoop('get_uid', ser)))
    uid = cmdLoop('get_uid', ser).strip().split()
    #print(f'uid is {uid}')
    uid = ' '.join(uid[:3])
    #print(cmdLoop('getmon', ser))
    temp = float(cmdLoop('getmon', ser).strip().split()[1])
    
    runInfo['uid'] = uid
    runInfo['temperature'] = temp
    runInfo['voltage'] = args.voltage
    runInfo['threshold'] = args.disc
    
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
            sys.exit()
    
    #mydatetime = datetime.datetime.now()
    #pretime = time.clock_gettime_ns(time.CLOCK_REALTIME)
    mytime2 = time.clock_gettime_ns(time.CLOCK_REALTIME)
    print(mytime2)
    
    #print(f'time to get python time = {time.clock_gettime_ns(time.CLOCK_REALTIME) - mytime}')
    runInfo['udaq_time'] = cmdLoop('print_time', ser).split('\n')[0]
    print(runInfo['udaq_time'])
    mytime = time.clock_gettime_ns(time.CLOCK_REALTIME)
    print(f'time to get udaq time = {mytime - mytime2}')
    #mytime = time.clock_gettime_ns(time.CLOCK_REALTIME) #time.time_ns()
    
    
    mydatetime = datetime.datetime.now()
    #runInfo['ppsTime'] = cmdLoop('print_pps',ser).split('\n')[0]
    mydate = str(mydatetime.date())
    #mytime = time.time_ns()#str(mydatetime.time().strftime("%H:%M:%S:%f"))
    
    runInfo['date'] = mydate
    runInfo['time'] = mytime
    subruns = int(round(args.runtime/float(subruntime), 0))
    if subruns <= 0 : subruns = 1
    runInfo['subruns'] = subruns
    
    # start and stop the run here
    data = []
    
    
    runInfo['runTimes'] = []
    runInfo['udaqTimeSubRuns'] = []
    cmdLoop('cputrig_width 2',ser)
    cmdLoop('set_cputrig_10mhz_enable 1',ser) #testing on
    cmdLoop('set_cputrig_enable 1',ser) #testing on
    
    cmdLoop('trigout_width 5',ser)
    cmdLoop('trigout_mode 2',ser) # 2 = trigger formed during buffer readout
    cmdLoop('set_livetime_enable 1', ser)
    print(time.time_ns())
    #runInfo['runTimes'].append("0 start " + str(time.time_ns()))
    cmdLoop('run 1 0 0', ser, 5)

    out = None
    rundir, runfile = getNextRun(args.PORT)
    
    # write out the binary
    
    
    bfile = open(os.path.join(rundir, runfile+'.bin'), 'wb')
    
    for i in range(subruns):
        #if i>0:
            #if cmdLoop('run 1 0 0', ser, 5) is None:
                #break
            
        print('INFO: running subrun {0} of {1}'.format(i+1, subruns))
        
        print('INFO: collecting data for {0} seconds...'.format(subruntime))
        time.sleep(subruntime)

        # In noisy environments or with really high rates
        # the stop command takes a number of retries before
        # the udaq actually processes the command.
        #print(time.time_ns())
        #runInfo['runTimes'].append(f'{i} end  {time.time_ns()}')
        
        #runInfo['udaq_timeSubRuns'].append(f'{i] end + {cmdLoop('print_time', ser).split('\n')[0]}')
        
        out = cmdLoop('stop_run', ser, 100)
        #cmdLoop('set_cputrig_enable 1',ser) #testing on
        #cmdLoop('set_cputrig_10mhz_enable 1',ser) #testing on
        #udaqTimeValue = cmdLoop("print_time", ser).split("\n")[0]
        #runInfo['udaqTimeSubRuns'].append(f'{i} end  {udaqTimeValue}')
        #out = cmdLoop('stop_run', ser, 100)
        if out is None:
            break
        stopRun = datetime.datetime.now()
        # the hex dump - useful for debugging
        #hdump = cmdLoop('dump_hits_hex 4096', ser, ntry=5, decode=True)
        #print(hdump)
        # print out the trigger rate
        #rate = getRate(ser)
        #print('INFO: trigger rate = {0} Hz'.format(rate))
       # if #rate > 0.0:
        #    runInfo['trigrate'] = rate
        
        dump = cmdLoop('dump_hits_binary', ser, ntry=5, decode=False)
        
        
        if i > -1:
            if dump is not None:
                #udaqTimeValue = cmdLoop("print_time", ser).split("\n")[0]
                #runInfo['udaqTimeSubRuns'].append(f'{i+1} start  {udaqTimeValue}')
                #cmdLoop('set_cputrig_enable 0',ser) #testing on
                #cmdLoop('set_cputrig_10mhz_enable 0',ser) #testing on
                cmdLoop('run 1 0 0', ser, 5)
                #print(time.time_ns())
                #runInfo['runTimes'].append(f'{i+1} start {time.time_ns()}')

                #print(f'time to next run {(datetime.datetime.now() - stopRun).total_seconds()}')
                data.append(dump)
                for dump in data:
                    bfile.write(cobsDecode(dump))

        data=[]
        
        
        
    if out is not None:
        cmdLoop('stop_run', ser, 100)
        #cmdLoop('trigout_mode 1',ser) #adding as test
        cmdLoop('set_cputrig_enable 1',ser) #testing on
        cmdLoop('set_cputrig_10mhz_enable 1',ser) #testing on
        cmdLoop('set_livetime_enable 0', ser)
        
        
        # paranoid safety measure - set voltage back to 0
        cmdLoop('auxdac 1 0', ser)
        cmdLoop('auxdac 1 0', ser)
    
    # close the serial connection
    closeSerial(ser)
    
    #if not len(data) > 0:
        #print('\nERROR: no data found, quitting...')
        #return

    # determine the run number and dir path/name
    
    
    # write the info to json
    with open(os.path.join(rundir, runfile+'.json'), 'w') as jfile:
        json.dump(runInfo, jfile, separators=(', ', ': '), indent=4)


    print('\n  SUCCESS: wrote data to [{0}]\n'.format(runfile))
    
    return


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


# flush and close the serial connection
def closeSerial(serial):
    serial.flushInput()
    serial.flushOutput()
    serial.close()


# try the command ntry times
def cmdLoop(msg, serial, ntry=15, decode=True):
    for i in range(ntry):
        serial.flushInput()
        serial.flushOutput()
        print(f'{msg} try {i}')
        serial.write((msg+'\n').encode())
        out = collect_output(serial, decode)
        #print(out)
        #print(type(out))
        if decode:
            if 'OK' in out:
                #time.sleep(.01)
                return out
            else:
                return out
                print("here here")
                #print(out)
                serial.flushInput()
                serial.flushOutput()
                #time.sleep(0.08)
        else:  
            if 'OK' in out[-4:].decode(): #errors="ignore" in decode()
                #print(out[-4:])
                return out
            else:
                serial.flushInput()
                serial.flushOutput()
                #time.sleep(0.05)
    print('ERROR: giving up')
    #closeSerial(serial)
    #return None


# A method of collecting the output with an interbyte timeout
def collect_output(serial, decode=True): 		
    slept = False
    if decode:
        out = ''
        
        
    else:
        out = bytearray()
        
    while True:
        n = serial.inWaiting()
        #print(n)
        #out += serial.read(n).decode()
        if n == 0:
            #continue
            #print('n=0 here')
            if not decode:
                if slept == True:
                    break
                #continue
                time.sleep(0.05)
                slept = not slept
            if decode:
                if slept == True:
                    #break
                    continue
                #time.sleep(0.1)
                slept = not slept
            

        else:
            #print("past n = 0")
            if decode:
                line = serial.readline()
                out += line.decode()
                #print(line)
                #print(out)
                serial.flushInput()
                serial.flushOutput()

                break
                #out += serial.readline().decode()
                #print(out)
            else:
                #time.sleep(0.05)
                out.extend(serial.read(n))
                #time.sleep(.05)
                #print('out =', bytes(out))
            slept = False
    #print("out of while")
    #print(out)
    return out


# set the next run number and output dir
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

def getNEvents(ser):
    stats = cmdLoop('get_run_statistics', ser).strip().split()
    events = int(stats[1])
    duration = float(stats[4])
    trigrate = events / duration
    return events
    
def getRate(ser):
    stats = cmdLoop('get_run_statistics', ser).strip().split()
    events = int(stats[1])
    duration = float(stats[4])
    trigrate = events / duration
    return round(trigrate, 1)



if __name__ == "__main__":
    main()

