#!/usr/bin/env python

import serial
import time


PORT = '/dev/ttyUSB0'


def main():
    
    ser = serial.Serial(port=PORT, baudrate=1000000)
    #ser.flushInput()
    #ser.flushOutput()
    
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

