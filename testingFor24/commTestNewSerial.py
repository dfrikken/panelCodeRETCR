#!/usr/bin/env python

import serial
import time
import argparse

#PORT = '/dev/ttyUSB0'


def main():
    
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--port', dest='PORT', type=str, default=0,
                    help='/dev/ttyUSB port to test comms with')
    args = ap.parse_args()
    PORT = '/dev/ttyUSB'+ args.PORT
    ser = serial.Serial(port=PORT, baudrate=1000000, parity=serial.PARITY_EVEN)
    #ser.flushInput()
    #ser.flushOutput()
    
    for cmd in ['get_uid', 'getmon']:
    #cmd = 'getmon'
        write(ser, cmd)
        out = read(ser)
        #temp = float(out.strip().split()[1])
        #print(temp)
        print(out)

    cmd = 'print_pps'
    write(ser, cmd)
    out = read(ser)
    cmd = 'debug 1'
    write(ser, cmd)
    out = read(ser)
    
    #ser.flushInput()
    #ser.flushOutput()
    ser.close()
    
    return


def write(ser, cmd):
    print(cmd)
    ser.write((cmd+'\r\n').encode())
    return


def read(ser):
    slept = False
    out = ''
    while True:
        n = ser.inWaiting()
        if n == 0:
            #continue
            #print('n=0 here')
            if slept == True:
                #break
                continue
            #time.sleep(0.1)
            slept = not slept
        else:
            
                line = ser.readline()
                out += line.decode()
                #print(line)
                print(out)
                ser.flushInput()
                ser.flushOutput()
                break
                #out += serial.readline().decode()
                #print(out)
    return out


if __name__ == "__main__":
    main()

