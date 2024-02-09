#!/usr/bin/env python

from struct import unpack
from cobs import cobs
import numpy as np
import argparse


def main():
    aparse = argparse.ArgumentParser()
    aparse.add_argument(dest='infiles', type=str, nargs="+", help='file name(s)')
    aparse.add_argument('--skip', dest='skip', type=int, default=0, help='skip X bytes at beginning')
    aparse.add_argument('--debug', dest='debug', type=int, default=0, help='debug output level [0-3]')
    aparse.add_argument('--nopps', dest='nopps', action='store_true', help='if no PPS to udaq')
    aparse.add_argument('--cobs', dest='cobs', action='store_true', help='cobs decode the data')
    
    args = aparse.parse_args()

    data = udaqChargestamps(args.infiles,
                            skip_bytes=args.skip,
                            debug=args.debug,
                            no_pps=args.nopps,
                            cobs_decode=args.cobs)

    events = len(data)
    duration = round(data[-1][0] - data[0][0], 1)
    if events > 0 and duration > 0:
        rate = round(events / duration, 1)
        print('{0} events in {1} seconds = {2} Hz'.format(events, duration, rate))
    else:
        print('{0} events in {1} seconds'.format(events, duration))
        
    return


def udaqChargestamps(infiles, skip_bytes=0, debug=0, no_pps=0, cobs_decode=0):
    data = []
    if isinstance(infiles, str):
        infiles = [infiles]
    if isinstance(infiles, list):
        for infile in infiles:
            data.extend(udaqDecode(infile,
                                   skip_bytes=skip_bytes,
                                   debug=debug,
                                   no_pps=no_pps,
                                   cobs_decode=cobs_decode).data)
    else:
        print('ERROR: Unsupported file type {0}, must be str or list'
              .format(type(infiles)))
    
    return data


class udaqDecode:

    OBJECT_CODE_PPS_SECOND   = 0xe0
    OBJECT_CODE_PPS_YEAR     = 0xe4
    OBJECT_CODE_TRIG_CONFIG  = 0xe5
    OBJECT_CODE_DATA_FORMAT  = 0xe6
    OBJECT_CODE_PAGE_END     = 0xe7
    OBJECT_CODE_HEADER       = 0xe8
    OBJECT_CODE_GENERIC      = 0xf0

    OBJECT_MASK_PPS_SECOND   = 0xfc
    OBJECT_MASK_GENERIC      = 0xf0

    STATUS_CPUTRIG_ACTIVE    = np.uint32(1<<5)

    DATA_FORMAT_TIMESTAMP               = 1
    DETAIL_TIMESTAMP_FINE               = (1<<0)
    DATA_FORMAT_TIMESTAMP_TOT_ADCS      = 2
    DATA_FORMAT_TIMESTAMP_TOT_ALL_CCRS  = 3

    N_ADCS = 3  # number of adcs to expect

    
    def __init__(self, infile, skip_bytes=0, debug=0, no_pps=0, cobs_decode=0):

        self.debug = debug
        # additional debugging
        self.print_pps = 0  # print all pps
        self.print_year = 0  # print all year

        self.no_pps = no_pps

        with open(infile, 'rb') as binFile:
            binout = binFile.read()

        if cobs_decode:
            binout = cobsDecode(binout, debug=1)
        
        # remove "OK" bytes if they still exist
        if 'OK' in binout[-4:].decode(errors='ignore'):
            print('INFO: cutting out \"OK\" bytes --> {0}'.format(binout[-4:]))
            binout = binout[:-4]

        if skip_bytes:
            print('INFO: skipping first {0} bytes'.format(skip_bytes))
            binout = binout[skip_bytes:]

        if debug > 1:
            print('header e8xxxxxx - year e4xxxxxx - pps e0xxxxxx - cpu e5xxxxxx')
            print('INFO: word 1: {0}'.format(binout[:4][::-1].hex()))
            print('INFO: word 2: {0}'.format(binout[4:8][::-1].hex()))
            print('INFO: word 3: {0}'.format(binout[8:12][::-1].hex()))

        nwords = len(binout)/4.
        if nwords != int(nwords):
            extra_bytes = int((nwords-int(nwords))*4)
            print('WARNING: Number of bytes not a factor of 4. {0} extra bytes: {1}'
                  .format(extra_bytes, binout[-extra_bytes:][::1].hex()))

        self.nwords = int(nwords)
        self.binout = binout
        self.data = []
        
        self.decodeData()


    def getWord(self, i):
        return np.uint32(unpack('<I', self.binout[i*4:i*4+4])[0])

    
    def phex(self, word):
        # pretty print hex
        hword = hex(word)[2:]
        hword = hword.zfill(8)
        hword = ('{0} {1} {2} {3}'
                 .format(hword[0:2].lower(),
                         hword[2:4].lower(),
                         hword[4:6].lower(),
                         hword[6:8].lower()
                         ))
        return hword

        
    def decodeData(self):

        year                = np.uint16(0)
        prev_year           = np.uint16(0)
        pps                 = np.uint64(0)
        prev_pps            = np.uint64(0)
        format_subtype      = np.uint16(0)
        format_detail_bits  = np.uint16(0)
        cputrig             = np.uint16(0)

        t  = np.uint64(0)
        t0 = np.float64(0)
        t1 = np.float64(0)

        time_errors = 0
        type_errors = 0
        nadc_errors = 0
        miss_errors = 0
        vals_errors = 0
        lbmo_errors = 0

        # skip first TIMESTAMP_TOT_ADCS because
        # it always has wrongs values, probably
        # a bug in the firmware initialization
        skip_first_hit = 1
        
        
        # loop over all the words
        index = 0
        while index < self.nwords:

            word = self.getWord(index)
            
            type_bits = np.uint8(word >> 24)

            # clock ticks sometimes rolls into generic space
            if type_bits < 0xe0 or (type_bits & self.OBJECT_MASK_GENERIC) == self.OBJECT_CODE_GENERIC:

                t = ((np.uint64(word)* 25.) / 72.) / 1.e9
                t1 = t + pps
                # check for linear time
                if t0 > t1:
                    if self.debug > 0:
                        print('WARNING: non-linear time t1-t0 = {0}'.format(t1-t0))
                    time_errors += 1
                t0 = t1
                
                if format_subtype == self.DATA_FORMAT_TIMESTAMP:
                    #if self.debug > 2:
                    print('{0} [{1}] TIMESTAMP - should never see these'
                          .format(self.phex(word), index))

                elif format_subtype == self.DATA_FORMAT_TIMESTAMP_TOT_ADCS:
                    # init these to -1 because of the 0-charge issue! 2022-01-28
                    tot = -1
                    adc1 = -1
                    adc2 = -1
                    adc3 = -1
                    n_adcs = 0
                    
                    if self.debug > 2:
                        print('{0} [{1}] TIMESTAMP_TOT_ADCS : {2:.9f}'
                              .format(self.phex(word), index, t1))

                    # grab next word
                    if index+1 < self.nwords:
                        index += 1
                        word = self.getWord(index)

                        n_adcs = (word >> 28) & 0xf

                        # grab the Time-over-Threshold
                        tot = (word >> 16) & 0xfff

                        # grab the first adc
                        adc1 = (word & 0xfff)
                        if self.debug > 2:
                            print('{0} [{1}]     tot={2}  adc1={3}'
                                  .format(self.phex(word), index, tot, adc1))
                    else:
                        miss_errors += 1
                        
                    # grab the next word if more adcs
                    if n_adcs > 1 and index+1 < self.nwords:

                        index += 1
                        word = self.getWord(index)

                        adc2 = (word >> 16) & 0xfff
                        
                        if n_adcs > 2:
                            adc3 = (word & 0xfff)
                            
                        if self.debug > 2:
                            print('{0} [{1}]     adc2={2}  adc3={3}'
                              .format(self.phex(word), index, adc2, adc3))
                    else:
                        miss_errors += 1
                        
                    # n_adcs should always be <= 3 for what we typically do
                    # remember each word contains 2 ADC values
                    if n_adcs > self.N_ADCS:
                        nadc_errors += 1
                        n_words = int(np.ceil((n_adcs-3)/2.))
                        if self.debug > 0:
                            print('WARNING: n_adcs = {0}'.format(n_adcs))
                        # don't skip extra adcs here because it's probably not
                        # the correct number of adcs anyway (buffer corruption)
                        #index += n_words

                    # check if adcs changed from -1
                    if n_adcs > 0 and adc1 == -1:
                        if self.debug > 0:
                            print('WARNING: ADC-1 still at -1')
                        vals_errors += 1
                    if n_adcs > 1 and adc2 == -1:
                        if self.debug > 0:
                            print('WARNING: ADC-2 still at -1')
                        vals_errors += 1
                    if n_adcs > 2 and adc3 == -1:
                        if self.debug > 0:
                            print('WARNING: ADC-3 still at -1')
                        vals_errors += 1

                    # append the list of chargestamps
                    #----------------------------------------------------------
                    if skip_first_hit:
                        skip_first_hit = 0
                    else:
                        if n_adcs > 0:
                            #self.data.append([t1, adc1, adc2, adc3, int(cputrig), tot])
                            # time-over-threshold doesn't seem to work correctly
                            self.data.append([t1, adc1, adc2, adc3, int(cputrig)])
                    #----------------------------------------------------------


                elif format_subtype == self.DATA_FORMAT_TIMESTAMP_TOT_ALL_CCRS:
                    # we should never see this in scint data
                    #if self.debug > 0:
                    print('{0} [{1}] TIMESTAMP_TOT_ALL_CCRS - should never see these'
                          .format(self.phex(word), index))
                    index += 17 

                else:
                    #if self.debug > 0:
                    print('{0} [{1}] unknown format_subtype {2}'
                          .format(self.phex(word), index, hex(format_subtype)))
                    type_errors += 1


            elif type_bits == self.OBJECT_CODE_PPS_YEAR:
                # PPS year word
                year = np.uint16(word)
                if abs(year - prev_year) > 1 and prev_year:
                    print('WARNING: year changed by {0} years'.format(year-prev_year))
                prev_year = year
                if self.debug > 1 or self.print_year:
                    print('{0} [{1}] PPS_YEAR : {2}'
                          .format(self.phex(word), index, year))

            elif (type_bits & self.OBJECT_MASK_PPS_SECOND) == self.OBJECT_CODE_PPS_SECOND:
                # PPS seconds word
                if self.no_pps:
                    # if using udaq without PPS, just increment by 1 to
                    # preserve linear time
                    pps += np.uint32(1)
                else:
                    pps = np.uint32(word & 0x03ffffff)

                if abs(pps - prev_pps) > 1 and prev_pps:
                    print('WARNING: pps changed by {0} seconds'.format(pps-prev_pps))
                prev_pps = pps
                if self.debug > 1 or self.print_pps:
                    print('{0} [{1}] PPS_SECOND : {2}'
                          .format(self.phex(word), index, pps))

            elif type_bits == self.OBJECT_CODE_DATA_FORMAT:
                # hit data format selector
                format_subtype = np.uint16((word & 0x00ff0000) >> 16)
                format_detail_bits = np.uint16(word & 0xffff)
                if self.debug > 1:
                    print('{0} [{1}] DATA_FORMAT : subtype={2} detail={3}'
                          .format(self.phex(word), index, hex(format_subtype),
                                  hex(format_detail_bits)))

            elif type_bits == self.OBJECT_CODE_TRIG_CONFIG:
                # config bits, that tells if live (not cpu trigger mode)
                cputrig = ((word & self.STATUS_CPUTRIG_ACTIVE) != 0)
                if self.debug > 1:
                    print('{0} [{1}] CPUTRIG : {3:.9f}'
                          .format(self.phex(word), index, cputrig, t1))
                # FIXME should handle this word correctly instead of skipping it?
                index += 1
                word = self.getWord(index)
                if self.debug > 1:
                    print('{0} [{1}] skipped word after cpu trig'
                          .format(self.phex(word), index))
                
            elif type_bits == self.OBJECT_CODE_HEADER:
                
                # header info is 1 word 
                
                # number of words in page
                num_words = ((word >> 10) & 0x3fff)
                
                # stream status
                # 0 = Start of Stream
                # 1 = Continuous running
                # 2 = buffer overflow
                # 3 = End of Stream
                status = ((word >> 8) & 0x3)
                
                # source id (given by field hub)
                sid = ((word) & 0xff)
                
                if self.debug > 1:
                    print('{0} [{1}] HEADER : nwords={2} status={3} sid={4}'
                          .format(self.phex(word), index, num_words, status, sid))
                    
                if status == 0:
                    if self.debug > 0:
                        print('INFO: Start of Stream flagged')
                        
                if status == 2:
                    lbmo_errors += 1
                    if self.debug > 1:
                        print('WARNING: buffer overflow')
                    
                if status == 3:
                    if self.debug > 0:
                        print('INFO: End of Stream flagged')
                
            elif (type_bits & self.OBJECT_MASK_GENERIC) == self.OBJECT_CODE_GENERIC:
                # these look like clock ticks rollover from 0xe0?
                #if self.debug > 0:
                print('{0} [{1}] OBJECT_CODE_GENERIC - skipping'
                      .format(self.phex(word), index))
                type_errors += 1
                
            else:
                #if self.debug > 0:
                print('{0} [{1}] unknown object type - skipping'
                      .format(self.phex(word), index))
                type_errors += 1
                
            index += 1

            
        ### show total errors
        if time_errors: print('WARNING: non-linear time errors =', time_errors)
        if nadc_errors: print('WARNING: n adcs > 3 errors =', nadc_errors)
        if miss_errors: print('WARNING: missing adc errors =', miss_errors)
        if type_errors: print('WARNING: object type errors =', type_errors)
        if vals_errors: print('WARNING: -1 charge errors =', vals_errors)
        if lbmo_errors: print('WARNING: buffer overflows =', lbmo_errors)


        
def cobsDecode(binary, debug=0):
                
    # find all the frame markers
    markers = []
    for i, val in enumerate(binary):
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
        cdata = binary[fstart+1:fstop]
        
        # cobs decode the frame
        data = cobs.decode(cdata)
        
        # grab the checksum for maybe checking later - trailing 2 bytes
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



if __name__ == "__main__":
    main()
