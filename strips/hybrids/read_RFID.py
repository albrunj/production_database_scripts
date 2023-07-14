#!/usr/bin/python
import os
import re
import sys
from collections import OrderedDict

try:
    import serial
except ImportError:
    print('Package \'serial\' is not installed!')
    print('')
    print('For python2, please run:')
    print('    sudo apt-get install python-serial')
    print('or:')
    print('    pip install pyserial')
    print('')
    print('For python3, please run:')
    print('    sudo apt-get install python3-serial')
    print('or:')
    print('    pip3 install pyserial')
    print('')
    print('Exiting.')
    sys.exit(1)

                        # SOH Len OPC Status RFU            # RSSI       # Tx/Rx      # Frequency  # Timestamp  # Phase      # Protocol         # RFU        # EPC len    # PC word    # EPC ID      # Tag CRC    # Message CRC
_REGEX_OLD = re.compile(r'(ff)(28)(22)(0000)(10031b01ff0101)([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{6})([0-9a-f]{8})([0-9a-f]{4})([0-9a-f]{2})(0000)([0-9a-f]{2})([0-9a-f]{4})([0-9a-f]{4})([0-9a-f]{24})([0-9a-f]{4})([0-9a-f]{4})')

                        # SOH Len OPC Status RFU+1bytes       # RSSI       # Tx/Rx      # Frequency  # Timestamp  # Phase      # Protocol         # RFU+3bytes # EPC len    # PC word    # EPC ID      # Tag CRC    # Message CRC
_REGEX_NEW = re.compile(r'(ff)(2c)(22)(0000)(8810031b0fff0101)([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{6})([0-9a-f]{8})([0-9a-f]{4})([0-9a-f]{2})(0000)([0-9a-f]{8})([0-9a-f]{4})([0-9a-f]{4})([0-9a-f]{24})([0-9a-f]{4})([0-9a-f]{4})')


def read_RFID(port, minreads = 3):
    if not os.path.exists(port):
        raise OSError('Port does not exist: %s' % port)
    s = serial.Serial(port = port, baudrate = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 2)
    s.flush()
    d = ''.join(['{:02x}'.format(l) for l in s.readline()])
    retval = OrderedDict()
    # Try the new FW return scheme first
    results = _REGEX_NEW.findall(d)
    if not results:
        # Else try the old FW return schemes
        results = _REGEX_OLD.findall(d)
        if not results:
            # No data?
            s.close()
            return retval
    if not all(results[0][15] == res[15] for res in results): # Assert all measured RFIDs are the same
        raise RuntimeError('Not all read RFIDs are the same: %s' % list(set([res[15] for res in results])))
    if len(results) < minreads:
        raise RuntimeError('Did not read the same RFID %s times, only read it %s times.' % (minreads, len(results)))
    (   retval['SOH'],
        retval['Length'],
        retval['OpCode'],
        retval['Status Word'],
        retval['RFU'],
        retval['RSSI'],
        retval['Tx/Rx Antenna'],
        retval['Frequency'],
        retval['Timestamp'],
        retval['Phase'],
        retval['Protocol'],
        retval['Embedded Data Length'],
        retval['RFU (2)'],
        retval['EPC Length'],
        retval['PC Word'],
        retval['EPC ID'],
        retval['Tag CRC'],
        retval['Message CRC']) = results[0]
    s.close()
    return retval

def main(port):
    retval = read_RFID(port)
    if retval:
        print('RFID: %s' % retval['EPC ID'])
        print('Detailed results:')
        for k in retval.keys():
            r = str(retval[k]) # Has to be its own line, for some reason?? - DON'T MOVE ME INTO THE STRING FORMATTING OF THE PRINT STATEMENT BELOW
            print('    %s : %s' % (k.rjust(max([len(k) for k in retval.keys()])), r))
    else:
        print('No data found! Are you holding the reader too far away from the chip or not holding it nearby long enough (1-2 seconds)? Please try again.')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'Read an RFID.', epilog = 'After starting the script, hold down the channel button of the ThingMagic reader and press the antenna to the RFID chip. If you cannot open the port, trying running the script with \'sudo\'.')
    parser.add_argument('-p', dest = 'port', type = str, default = '/dev/ttyACM0', help = 'Path to the serial port the ThingMagic reader is connected to (e.g., /dev/ttyACM0 on Linux).')
    args = parser.parse_args()
    sys.exit(main(args.port))
