#!/usr/bin/env python

# monitor.py
# 2016-09-17
# Public Domain

# monitor.py          # monitor all GPIO
# monitor.py 23 24 25 # monitor GPIO 23, 24, and 25

import sys
import time
import pigpio

last = [None]*32
cb = []

f = open("hitBufferMode/runs/gpioMonitor.txt", "w")
myList = []
def cbf(GPIO, level, tick):
   if last[GPIO] is not None:
      diff = pigpio.tickDiff(last[GPIO], tick)
      
      f.write(f'{GPIO},{time.clock_gettime_ns(time.CLOCK_REALTIME)}\n')
      #f.write(f'{GPIO},{time.time_ns()}\n')
      #myList.append(f'{GPIO},{tick}\n')
      #f.write(f'{GPIO},{tick}\n')
      #print("G={} l={} d={} ".format(GPIO, level, diff))
      print("G={} l={} t={} ".format(GPIO, level, tick))
   last[GPIO] = tick

pi = pigpio.pi()

if not pi.connected:
   exit()

if len(sys.argv) == 1:
   G = range(15, 25)
else:
   G = []
   for a in sys.argv[1:]:
      G.append(int(a))
   
for g in G:
   cb.append(pi.callback(g, pigpio.RISING_EDGE, cbf))

try:
   while True:
      time.sleep(6000)
except KeyboardInterrupt:
   for i in myList:
      #print(i)
      f.write(i)
   print("\nTidying up")
   for c in cb:
      c.cancel()
   f.close()

pi.stop()

