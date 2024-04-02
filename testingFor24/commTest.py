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
    ser = serial.Serial(port=PORT, baudrate=1000000, parity=serial.PARITY_EVEN,timeout=3)
    ser.flushInput()
    ser.flushOutput()
    #print('flushed')
    
    for cmd in ['get_uid', 'getmon']:
        write(ser, cmd)
        out = read(ser)
        print(out)
    
    
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
            if slept == True:
                break
            time.sleep(0.05)
            slept = not slept
        else:
            out += ser.read(n).decode()
            slept = False
    return out


if __name__ == "__main__":
    main()

