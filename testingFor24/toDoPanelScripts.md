Edits to panel python scripts:

    fix hardcoded directories

    write each panel its own data taking script
        sometimes the importing of variables isnt correct, seperate files ensures both panels are going correctly


    DONE -1. convert all times to time.time_ns() and clean the hour cycling 
    DONE -2. txt file out for buffer read out times
    3. error catching and file out monitoring
    4. bias voltage sweep and threshold sweep finer
        - some way to correct gain on the fly?
    DONE -5. change /dev/ttyUSB* to device ID 
    DONE -6. write error catching function that reacts and takes over on uDAQ going unresponsive.
        - for now just flag the error and alert terminal that 24v power cycle is required
        - for field use need this automatic, record time this happened
    DONE -7. Monitor function that dumps important info to log

    DONE -#check hang up on reading (probably need a catch on serial.readline)
        This seems to be fixed, i added a condition to flush serial output 



Tests to run
    DONE - baud rate in default is most stable 1. Baud rate of py script testing ( is 1e6 too high??) data sheet for ttl cables say 3MBaud is highest rate
    - done works well 2. even parity test
    3. trigger out length stability testing
    4. stress test new serial comms
    5. check for memory leaks in python


GPIO pin notes

    TO DO:
        - rewrite to seperate pins hardcoded, sometimes it seems to assign the gpio monitor to the same pin 
            DONE- fix c version to rising edge (write command needs length of string change 4 to 6)

            DONE- write initialize function using zero bias voltage and scheduled triggers to latch time then move into run testing two panel coincidence

            DONE- more testing with signal generator (fix ground floating)

            DONE- test with all timestamps throughout run
                - seems to work fine

 
    the pigpio package (python) seems a bit unreliable so far, using the monitor.py version from the pigpio examples. It misses quite a lot of triggers edges regardless of edge set to rising, falling or either. C version seems to be better

    I tested both python and c so far with panel triggers and signal generator. 

        panel use:
            when using the panel triggers im able to see triggers and apply timestamps to both python and C but the python triggers miss a good amount. initially the C version only had both edges avalable so the timing was tough to determine, but Cosmin suggested a way to fix it to rising edge that i will be implementing. The C version is lightweight fast and seems a bit better at latching triggers



        Signal generator:
            So im able to see triggers in both c and python, but c is more reliable here again. I can check the time difference between triggers to compare with the output Hz. There is some ground issue here though ive got to figure out. periodically the GPIO monitors will spam with ~16000 ns triggers ( i dont see these on the panels) 