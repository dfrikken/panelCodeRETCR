#!/usr/bin/env python

import sys
import os
import argparse
import time
import glob
import serial
import datetime


def main():
        
        ap = argparse.ArgumentParser()
        ap.add_argument('-p', '--port', dest = 'PORT', type = int, default = 0,
                        help = '/dev/ttyUSB port to start histogram mode in')
        ap.add_argument('-t', '--time', dest='runtime', type=int, default=10,
                help='data acquisition time in seconds (default is 10 seconds)')
        ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2650,
                help='voltage setting in daq units (default is 2650)')
        #adjusting default to stop crash
        ap.add_argument('-d', '--disc', dest='disc', type=int, default=1500,
                help='discriminator setting in daq units (default is 1370)')
        
        args = ap.parse_args()

        PORT = '/dev/ttyUSB'+str(args.PORT)

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
        
        commands = [
                'stop_run',
                'set_livetime_enable 0',
                'reset_schedule',
                'adc_reset_thresholds',
        ]
        
        for msg in commands:
                cmdLoop(msg, ser, 5)
                
        uid = cmdLoop('get_uid', ser).strip().split()
        uid = ' '.join(uid[:3])
        temp = cmdLoop('getmon', ser).strip().split()[1]
        
        commands = [
                'auxdac 1 {0}'.format(args.voltage),
                'dac 1 {0}'.format(args.disc),

                'timestamp_mode 0',
                'disc_opm 1',
                
                'adc_timer_delay 0 18',
                'adc_timer_delay 1 136',
                'adc_timer_delay 2 18',
                'adc_timer_delay 3 136',
                'adc_timer_delay 4 18',
                'adc_timer_delay 5 136',
                'adc_timer_delay 6 136',
                'adc_timer_delay 7 136',

                'adc_hist_enable 1',
                'hist_set_adc_masked 0 0 3',
                'hist_set_adc_masked 1 2 3',
                'hist_set_adc_masked 2 12 3',
        ]
        
        for msg in commands:
                cmdLoop(msg, ser)

        # start and stop the run here
        cmdLoop('set_livetime_enable 1', ser)
        cmdLoop('run 1 0 0', ser)
        print('waiting {0} seconds...'.format(args.runtime))
        time.sleep((args.runtime))
        cmdLoop('stop_run', ser, 5)
        cmdLoop('set_livetime_enable 0', ser)

        # paranoid safety measure - set voltage back to 0
        cmdLoop('auxdac 1 0', ser)

        # dump the data
        hists = []
        hists.append(cmdLoop('hist_dump 0', ser, 5))
        hists.append(cmdLoop('hist_dump 1', ser, 5))
        hists.append(cmdLoop('hist_dump 2', ser, 5))

        # grab the run statistics
        stats = cmdLoop('get_run_statistics', ser).strip().split()
        events = int(stats[1])
        duration = float(stats[4])
        trigrate = events / duration

        print('Port {0} trigger rate = {1} Hz'.format(args.PORT,round(trigrate, 1)))
        
        # close the serial connection
        closeSerial(ser)

        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        mytime = str(mydatetime.time().strftime("%H:%M:%S"))

        # write stuff out to file(s)
        rundir, runfile = getNextRun(str(args.PORT))
        for adc in range(len(hists)):
                with open(os.path.join(
                                rundir,
                                '{0}_adc{1}_hist.dat'
                                .format(runfile, adc)), 'w') as out:
                        
                        # log some info the file
                        out.write("# runnum = {0}\n".format(runfile))
                        out.write("# date = {0}\n".format(mydate))
                        out.write("# time = {0}\n".format(mytime))
                        out.write("# uid = {0}\n".format(uid))
                        out.write("# temperature = {0}\n".format(temp))
                        out.write("# threshold = {0}\n".format(args.disc))
                        out.write("# voltage = {0}\n".format(args.voltage))
                        out.write("# events = {0}\n".format(events))
                        out.write("# duration = {0}\n".format(duration))
                        out.write("# trigrate = {0}\n".format(trigrate))
                        out.write("# ADC-{0}\n".format(adc))
                        
                        # write the histogram
                        for line in hists[adc].split('\n'):
                                info = line.split(' ')
                                try:
                                        out.write("{0} {1}\n".format(int(info[0]), int(info[1])))
                                except:
                                        continue
                                
        print('\nSUCCESS --> {0}\n'.format(rundir))


# flush and close the serial connection
def closeSerial(serial):
        serial.flushInput()
        serial.flushOutput()
        serial.close()

        
# try the command ntry times
def cmdLoop(msg, serial, ntry=3):
        for i in range(ntry):
                print(msg)
                serial.write((msg+'\r\n').encode())
                out = collect_output(serial)
                if 'OK' in out:
                        return out
                print(out)
        print('some error?')
        closeSerial(serial)
        sys.exit()
        

# A method of collecting the output with an interbyte timeout
def collect_output(serial):
        slept = False
        out = ''
        while True:
                n = serial.inWaiting()
                if n == 0:
                        if slept == True:
                                break
                        time.sleep(0.04)
                        slept = not slept
                else:
                        out += serial.read(n).decode()
                        slept = False
        return out
    

# set the next run number and output dir
def getNextRun(port ,runsdir='runs'):
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(here, runsdir)):
                lastrun = sorted(glob.glob(os.path.join(here, runsdir, f'port{port}_run_*')))
                if lastrun:
                        lastrun = int(lastrun[-1].split('run_')[-1])
                else:
                        lastrun = 0
        else:
                lastrun = 0
        run = 'port{0}_run_{1}'.format(port,str(lastrun+1).zfill(7))
        rdir = os.path.join(here, runsdir, run)
        os.makedirs(os.path.join(here, runsdir, run))
        return rdir, run

        
if __name__ == "__main__":
        main()

