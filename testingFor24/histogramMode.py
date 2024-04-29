#!/usr/bin/env python

import sys
import os
import argparse
import time
import glob
import serial
import datetime
import hitBufferDefine as hit

def main(useArgs = 1, panelToRun=0,disc=1700,voltage=2680,runTime=30,rateFile=''):
        hit.testFunction(300)
         #arguments for the run
        ap = argparse.ArgumentParser()
        ap.add_argument('-t', '--time', dest='runtime', type=int, default=3)
        ap.add_argument('-v', '--voltage', dest='voltage', type=int, default=2650)
        ap.add_argument('-d', '--disc', dest='disc', type=int, default=1710)
        ap.add_argument('-p','--panel',dest="panel",type=int,default=0)
        args = ap.parse_args()

        if args.panel!=0:
            panelToRun = args.panel

        #print(args)
        if useArgs ==0:
            args.disc = disc
            args.voltage = voltage
            args.runtime = runTime

        #print(args)
            
        print(f'running panel {panelToRun}')
        #args.disc = disc
        #args.voltage = voltage
           
        id12 = 'usb-FTDI_TTL-234X-3V3_FT76I7QF-if00-port0'
        id3 = 'usb-FTDI_TTL-234X-3V3_FT76S0N6-if00-port0'

        if panelToRun ==12:
            PORT = '/dev/serial/by-id/'+ id12
            
        if panelToRun ==3:
            PORT = '/dev/serial/by-id/'+ id3
    
        #print(args)
        # voltage sanity check
        if args.voltage > 2900:
            print('ERROR: voltage setting should never need to be >2800')
            sys.exit()

        # connect to udaq via USB
        try:
            ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE, timeout=3,stopbits=1)
            ser.flushInput()
            ser.flushOutput()
        except:
            print("ERROR: is the USB cable connected?")
            #hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
            sys.exit() #commented for testing
            
        print('serial connection made')
        ser.flushInput()
        ser.flushOutput()
        
        commands = [
                'stop_run',
                'set_livetime_enable 0',
                'reset_schedule',
                'adc_reset_thresholds',
        ]
        
        for msg in commands:
                hit.cmdLoop(msg, ser, 5)
                
        uid = hit.cmdLoop('get_uid', ser).strip().split()
        uid = ' '.join(uid[:3])
        temp = hit.cmdLoop('getmon', ser).strip().split()[1]
        
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
                hit.cmdLoop(msg, ser)

        # start and stop the run here
        hit.cmdLoop('set_livetime_enable 1', ser)
        hit.cmdLoop('run 1 0 0', ser)
        #print('waiting {0} seconds...'.format(args.runtime))
        time.sleep((args.runtime))
        hit.cmdLoop('stop_run', ser, 5)
        hit.cmdLoop('set_livetime_enable 0', ser)

        # paranoid safety measure - set voltage back to 0
        hit.cmdLoop('auxdac 1 0', ser)

        # dump the data
        hists = []
        hists.append(cmdLoop('hist_dump 0', ser, 5))
        hists.append(cmdLoop('hist_dump 1', ser, 5))
        #hists.append(cmdLoop('hist_dump 2', ser, 5))

        # grab the run statistics
        stats = cmdLoop('get_run_statistics', ser).strip().split()
        events = int(stats[1])
        duration = float(stats[4])
        trigrate = events / duration
        #print(f'panel{panelToRun} writing {args.voltage},{args.disc},{round(trigrate,2)},{temp}\n')
        print('Panel {0} trigger rate = {1} Hz'.format(panelToRun,round(trigrate, 1)))

        if '.txt' in rateFile:
            
            if not os.path.isfile(rateFile):
                #print(rateFile)
                with open(rateFile,'w') as rf:
                    rf.write('voltage,threshold,trigRate,temp\n')
                    rf.write(f'{args.voltage},{args.disc},{round(trigrate,2)},{temp}\n')
                    
            else:
                with open(rateFile,'a') as rf:
                    rf.write(f'{args.voltage},{args.disc},{round(trigrate,2)},{temp}\n')
                    #print(f'writing {args.voltage},{args.disc},{round(trigrate,2)},{temp}\n')
        
        # close the serial connection
        closeSerial(ser)

        mydatetime = datetime.datetime.now()
        mydate = str(mydatetime.date())
        mytime = str(mydatetime.time().strftime("%H:%M:%S"))

        # write stuff out to file(s)
        rfSplit = rateFile.split('/')
        #print(f'rate file is {rfSplit}')
        rateDir = f'{rfSplit[0]}/{rfSplit[1]}/{rfSplit[2]}/{rfSplit[3]}/histogramRuns'
        rundir, runfile = getNextRun(panelToRun,rateDir)
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
                #print(msg)
                serial.write((msg+'\r\n').encode())
                out = collect_output(serial)
                if 'OK' in out:
                        return out
                #print(out)
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
def getNextRun(panelToRun ,runsdir='runs/histogram'):
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(here, runsdir)):
                lastrun = sorted(glob.glob(os.path.join(here, runsdir, f'panel{panelToRun}_run_*')))
                if lastrun:
                        lastrun = int(lastrun[-1].split('run_')[-1])
                else:
                        lastrun = 0
        else:
                lastrun = 0
        run = 'panel{0}_run_{1}'.format(panelToRun,str(lastrun+1).zfill(7))
        rdir = os.path.join(here, runsdir, run)
        os.makedirs(os.path.join(here, runsdir, run))
        return rdir, run

        
if __name__ == "__main__":
        main()

