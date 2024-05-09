#!/usr/bin/env python


import sys
import os
import argparse
import time
import glob
import serial
from datetime import datetime, timedelta
import json
from cobs import cobs
import hitBufferDefine as hit
import numpy as np
import signal
from threading import Thread
import math
from multiprocessing import Process
import subprocess
from subprocess import PIPE, Popen

def main(port = 0):
    hit.testFunction(300)

    panel = 3
    #temp3 = hit.getPanelTemp(panel)
    #print(temp3)

    settingsList = hit.getThresholdAndVoltage(panel,30)
    print(settingsList)
    

    panel = 12
    #temp3 = hit.getPanelTemp(panel)
    #print(temp3)

    settingsList = hit.getThresholdAndVoltage(panel,30)
    print(settingsList)


 usb-FTDI_TTL-234X-3V3_FT76GULV-if00-port0
usb-FTDI_TTL-234X-3V3_FT76S1SV-if00-port0
    

    '''
    id3 = 'usb-FTDI_TTL-234X-3V3_FT76S0N6-if00-port0'
    PORT = '/dev/serial/by-id/'+ id3
    try:
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_EVEN, timeout=3)
        #ser.timeout = 1
        #ser.flushInput()
        #ser.flushOutput()
    except:
        print("ERROR: is the USB cable connected?")
        hit.errorLogger("FATAL ERROR error connecting to uDAQ over serial")
        sys.exit() #commented for testing
    print('serial connection made')


    panel = hit.panelIDCheck(ser)
                
    ser.close()
    
    
    '''
    
    
    
    
    
   
if __name__ == "__main__":
    main()



#!/usr/bin/env python


import sys
import os
import argparse
import time
import glob
import serial
from datetime import datetime, timedelta
import json
from cobs import cobs
import hitBufferDefine as hit
import numpy as np
import signal
from threading import Thread
import math
from multiprocessing import Process
import subprocess
from subprocess import PIPE, Popen

def main():
        hit.testFunction(300)

        #hit.powerCycle()

        #time.sleep(1)
        #hit.panelStartup()
        id1 = 'usb-FTDI_TTL-234X-3V3_FT76GULV-if00-port0'
        id2 - 'usb-FTDI_TTL-234X-3V3_FT76S1SV-if00-port0'

        PORT = '/dev/serial/by-id/'+ id1
        # connect to udaq via USB
        ser = serial.Serial(port=PORT, baudrate=1000000,parity = serial.PARITY_NONE, timeout=3,stopbits=1)
        ser.flushInput()
        ser.flushOutput()
        panel = hit.panelIDCheck(ser)
        print(panel)

        #id1 = 'usb-FTDI_TTL-234X-3V3_FT76GULV-if00-port0'