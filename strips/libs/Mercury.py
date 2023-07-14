#!/usr/bin/env python
import collections

import numpy as np
import serial

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += 1 # use start += 1 to find overlapping matches

def list_duplicates(seq):
    tally = collections.defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items()
            if len(locs) > 1)

def map_data(data):
    try:
        locations = list(find_all(str(data.hex()), "2822000010031b01ff0101"))
        locations = list(map(lambda x: x + 8, locations))
        locations = locations[:-1]
        temp = list(map(lambda x: x + 14, locations))
        RSSIList = list(map(lambda x: int(data.hex()[x:x + 2], 16), temp))
        temp = list(map(lambda x: x + 26 * 2, locations))
        temp2 = list(map(lambda x: int(int(data.hex()[x + 22 * 2:x + 22 * 2 + 4],16)/ 4 - 8), locations))
        EPCList = list(map(lambda x, y: data.hex()[x:x + y], temp, temp2))
        return EPCList, RSSIList
    except:
        return [],[]

def find_Tag(EPCList,RSSIList):
    try:
        indices = list(list_duplicates(EPCList))
        RSSIList = np.array(RSSIList)
        mean = []
        mostRead = 0
        for n,i in enumerate(indices):
            mean.append(
                sum(RSSIList[i[1]]) / float(len(RSSIList[i[1]]))
            )
            if len(indices[mostRead][1])< len(i[1]):
                mostRead = n
        largeRSSI = mean.index(max(mean))
        if largeRSSI == mostRead:
            return indices[largeRSSI][0], mean[largeRSSI]
        elif len(indices[mostRead][1]) > len(indices[largeRSSI][1])*1.2:
            return '',''
        else:
            return indices[largeRSSI][0], mean[largeRSSI]
    except:
        return [],[]


def read (usedTags, infoFromLastRead):

    ser = serial.Serial('/Com5',
                    baudrate=115200,
                    timeout=None)

    if ser.isOpen():
       # print("connected to reader!")
        pass
    else:
        return 0

    if infoFromLastRead == []:
        data = b""
    else:
        data = infoFromLastRead

    data += ser.readline()
    ser.close()
    if len(data) < 700:
        return data,"404"
    else:
        EPCList, RSSIList = map_data(data)
        EPC, RSSI = find_Tag(EPCList, RSSIList)

        # If the Tag is the same that was read before do not read it again!
        if EPC in usedTags:
            return '',''

        # Make beep sound to show that tag has been read sucessfully
        #print("\a")
        return EPC, RSSI
