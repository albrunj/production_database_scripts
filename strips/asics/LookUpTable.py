#!/usr/bin/env python

class DieType:
    __slots__ = ['SC_ASIC_ABC', 'SC_ASIC_HCC', 'SC_ASIC_AMAC', 'DieTypeError']
    SC_ASIC_ABC  = 0
    SC_ASIC_HCC  = 1
    SC_ASIC_AMAC = 2
    class DieTypeError(Exception):
        def __init__(self, *args, **kwargs):
            super(DieType.DieTypeError, self).__init__(*args, **kwargs)

class WaferSeries:
    __slots__ = ['SC_WAFER_DEFAULT', 'SC_WAFER_PROTOTYPE', 'WaferSeriesError']
    SC_WAFER_DEFAULT   = 0
    SC_WAFER_PROTOTYPE = 1
    class WaferSeriesError(Exception):
        def __init__(self, *args, **kwargs):
            super(WaferSeries.WaferSeriesError, self).__init__(*args, **kwargs)

class LookUpTable(object):

    __slots__ = ['int_die_type_2_asic_name_map', 'die_type_2_die_max_map', 'known_wafer_series', 'wafer_name_2_id_map']

    def __init__(self, *args, **kwargs):
        super(LookUpTable, self).__init__(*args, **kwargs)
        self.int_die_type_2_asic_name_map = {DieType.SC_ASIC_ABC: 'ABCStar', DieType.SC_ASIC_HCC: 'HCCStar', DieType.SC_ASIC_AMAC: 'AMAC'}
        self.die_type_2_die_max_map       = {DieType.SC_ASIC_ABC: 378, DieType.SC_ASIC_HCC: 98, DieType.SC_ASIC_AMAC: 96}
        self.known_wafer_series           = [WaferSeries.SC_WAFER_DEFAULT, WaferSeries.SC_WAFER_PROTOTYPE]
        self.wafer_name_2_id_map          = {}
        self.wafer_name_2_id_map[DieType.SC_ASIC_ABC] = {'VJCVPXH': 0,
                                                         'VQCVRQH': 1,
                                                         'VTCVRMH': 2,
                                                         'VPCVRRH': 3,
                                                         'V0CVRFH': 4,
                                                         'V2CVRDH': 5,
                                                         'V7CVR8H': 6,
                                                         'V1CVREH': 7,
                                                         'VKCVPWH': 8,
                                                         'VXCVQ1H': 9,
                                                         'VUCVRLH': 10,
                                                         'VSCVRNH': 11,
                                                         'VXCVRIH': 12,
                                                         'VICVPYH': 13,
                                                         'VMCVPUH': 14,
                                                         'VHCVPZH': 15
                                                        }

    def __checkDieType(self, die_type):
        if not (die_type in self.int_die_type_2_asic_name_map.keys() and die_type in self.die_type_2_die_max_map.keys() and die_type in self.wafer_name_2_id_map.keys()):
            raise DieType.DieTypeError('Unknown die type: %s' % die_type)
        return

    def __checkWaferNumber(self, die_type, wafer_number):
        if wafer_number not in self.wafer_name_2_id_map[die_type].keys():
            raise KeyError('Unknown wafer number for die type %s (\'%s\'): %s' % (die_type, self.int_die_type_2_asic_name_map[die_type], wafer_number))
        return

    def __checkWaferSeries(self, wafer_series):
        if wafer_series not in self.known_wafer_series:
            raise WaferSeries.WaferSeriesError('Unknown wafer series: %s' % wafer_series)
        return

    def getFuseIDs(self, die_type, wafer_number, wafer_series = WaferSeries.SC_WAFER_DEFAULT):
        # Perform checking on input args
        self.__checkDieType(die_type)
        self.__checkWaferNumber(die_type, wafer_number)
        self.__checkWaferSeries(wafer_series)
        # Get the wafer ID (int) and the max number of ASICs/wafer
        wafer_id = self.wafer_name_2_id_map[die_type][wafer_number]
        die_max  = self.die_type_2_die_max_map[die_type]
        # Start to build our fuseID header
        fuse_id_header = (wafer_id << 11)
        if wafer_series == WaferSeries.SC_WAFER_PROTOTYPE:
            fuse_id_header += (die_type << 9)
        elif wafer_series == WaferSeries.SC_WAFER_DEFAULT:
            fuse_id_header += (DieType.SC_ASIC_AMAC << 9)
        else:
            raise Exception('Shouldn\'t arrive here!')
        # Finally, iterate over all ASICs on the wafer and return
        fuse_ids = []
        for i in range(1, die_max + 1):
            fuse_ids.append(fuse_id_header + i)
        return fuse_ids

if __name__ == '__main__':
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent = 1, width = 200)
    lut = LookUpTable()
    fuse_ids = lut.getFuseIDs(die_type = DieType.SC_ASIC_ABC, wafer_number = 'VJCVPXH', wafer_series = WaferSeries.SC_WAFER_PROTOTYPE)
    pp.pprint([hex(i) for i in fuse_ids])
