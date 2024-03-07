Edits to panel python scripts:
    1. convert all times to time.time_ns() and clean the hour cycling 
        - change run open from sleep time to number of events 
    2. txt file out for buffer read out times
    3. error catching and file out monitoring
    4. bias voltage sweep and threshold sweep finer
        - some way to correct gain on the fly?
    5. change /dev/ttyUSB* to device ID 
    6. 

    #check hang up on reading (probably need a catch on serial.readline)
    



Tests to run
    1. Baud rate of py script testing ( is 1e6 too high??) data sheet for ttl cables say 3MBaud is highest rate
    2. even parity test
    3. trigger out length stability testing
    4. stress test new serial comms
    5. check for memory leaks in python
