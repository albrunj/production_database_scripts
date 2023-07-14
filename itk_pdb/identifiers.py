#!/usr/bin/python
from requests.exceptions import RequestException

from itk_pdb.dbAccess import ITkPDSession

_XX_STRIPS = ['SB', 'SE', 'SG']
_XX_PIXELS = ['PB', 'PE', 'PG']
_XX = _XX_STRIPS + _XX_PIXELS
_YY_STRIPS_OLD = ['01', '3L', '3R', '4L', '4R', '5L', '5R', 'AA', 'AM', 'CP', 'CW', 'F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'FA', 'FB', 'FC', 'FS', 'FX', 'FY', 'GL', 'GP',
                    'H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'HA', 'HB', 'HC', 'HT', 'HX', 'HY', 'LS', 'M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'ML', 'MS', 'N0', 'N1', 'N2', 'N3',
                    'N4', 'N5', 'NB', 'P0', 'P1', 'P2', 'P3', 'P4', 'PF', 'PP', 'S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'SD', 'SL', 'SS', 'SX', 'T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'TC', 'TF', 'TG',
                    'TL', 'TS', 'VB', 'VL', 'VS', 'WT', 'YZ', 'ZZ']
_YY_PIXELS_OLD = ['B1', 'B2', 'B4', 'BB', 'BC', 'BQ', 'BR', 'BS', 'BT', 'CB', 'CP', 'Cb', 'DP', 'EB', 'ES', 'FC', 'FL', 'FP', 'FW', 'GT', 'GU', 'HR', 'HS', 'HV', 'LM', 'LO', 'LV', 'M0', 'M1',
                    'M2', 'M5', 'MS', 'OB', 'Ob', 'Oc', 'P0', 'P5', 'PC', 'PD', 'PP', 'PQ', 'PS', 'PT', 'Pb', 'R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'RA', 'RB', 'S0', 'S1',
                    'S2', 'S3', 'S6', 'S7', 'S8', 'S9', 'SB', 'SF', 'SG', 'SH', 'SI', 'SJ', 'ST', 'SU', 'SV', 'SW', 'TP', 'TR', 'TZ', 'Tb', 'W0', 'W1', 'W2', 'W3', 'W6', 'W7', 'W8', 'WD', 'WP',
                    'YZ', 'ZZ', 'lp']
_YY_STRIPS = []
_YY_PIXELS = []

def checkComponentCode(component_code):
    if (len(component_code) == 32) and component_code.isalnum():
        return True
    else:
        return False

def checkSerialNumber(serial_number, update_yy = True, session = None):
    if update_yy and session:
        global _YY_STRIPS
        global _YY_PIXELS
        if not _YY_STRIPS:
            for ct in session.doSomething('listComponentTypes', 'GET', {'project': 'S'}):
                if ct.get('snComponentIdentifier') is not None:
                    _YY_STRIPS.append(ct['snComponentIdentifier'])
                if ct.get('types') is not None:
                    for st in ct.get('types', []):
                        if st.get('snComponentIdentifier') is not None and st['snComponentIdentifier'] != '':
                            _YY_STRIPS.append(st['snComponentIdentifier'])
            _YY_STRIPS = sorted(list(set(_YY_STRIPS)))
        if not _YY_PIXELS:
            for ct in session.doSomething('listComponentTypes', 'GET', {'project': 'P'}):
                if ct.get('snComponentIdentifier') is not None:
                    _YY_PIXELS.append(ct['snComponentIdentifier'])
                if ct.get('types') is not None:
                    for st in ct.get('types', []):
                        if st.get('snComponentIdentifier') is not None and st['snComponentIdentifier'] != '':
                            _YY_PIXELS.append(st['snComponentIdentifier'])
            _YY_PIXELS = sorted(list(set(_YY_PIXELS)))

        yy_strips = _YY_STRIPS
        yy_pixels = _YY_PIXELS
    else:
        yy_strips = _YY_STRIPS_OLD
        yy_pixels = _YY_PIXELS_OLD
    if ((len(serial_number) == 14) and (serial_number[0:3] == '20U') and (serial_number[3:5] in _XX) and (serial_number[5:7] in (yy_strips if serial_number[3:5] in _XX_STRIPS else yy_pixels)) and serial_number[7:].isdigit()):
        return True
    else:
        return False

def checkRFID(rfid):
    if (len(rfid) == 24) and rfid.isalnum():
        return True
    else:
        return False

def get_localname_codes():
    return ['LOCAL_NAME', 'LOCALNAME']

def get_rfid_codes():
    return ['RFID']

_LOCALNAME_CODES = get_localname_codes()
_RFID_CODES      = get_rfid_codes()

def get_component(session, identifier, component_types = []):
    if not isinstance(session, ITkPDSession): raise RuntimeError
    identifier = str(identifier)
    if checkComponentCode(identifier) or checkSerialNumber(identifier, session = session):
        try:
            component = session.doSomething('getComponent', 'GET', {'component': identifier, 'state': 'ready'})
        except RequestException:
            component = {}
    else:
        try:
            component = session.doSomething('getComponent', 'GET', {'component': identifier, 'state': 'ready', 'alternativeIdentifier': True})
        except RequestException:
            components = []
            for code in _LOCALNAME_CODES + _RFID_CODES:
                if code in _RFID_CODES:
                    identifier = identifier.upper()
                kwargs = {'filterMap': {'project': 'S', 'state': 'ready', 'outputType': 'object', 'propertyFilter': [{'code': code, 'operator': '=', 'value': identifier}]}}
                if component_types:
                    kwargs.update({'componentType': [ct['code'] for ct in component_types]})
                # Hack for string properties == '0' - is there ever a reason why the local object name or RFID would be 0?
                components += [c for c in session.doSomething('listComponentsByProperty', 'GET', kwargs) if any(p['code'] == code and p['value'] != '0' for p in c['properties'])]
            if len(components) == 1:
                component = get_component(session, components[0]['code'], component_types)
            else:
                component = {}
    if component and (component['componentType']['code'] not in [ct['code'] for ct in component_types] if component_types else False or component['state'] == 'deleted'):
        component = {}
    return component
