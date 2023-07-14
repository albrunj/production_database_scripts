#!/usr/bin/python
import sys

from read_RFID import read_RFID
from requests.exceptions import RequestException

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

from itk_pdb.dbAccess import ITkPDSession
from itk_pdb.identifiers import get_component
from itk_pdb.identifiers import get_localname_codes
from itk_pdb.identifiers import get_rfid_codes

try:
    input = raw_input
except NameError:
    pass

_LOCALNAME_CODES = get_localname_codes()
_RFID_CODES      = get_rfid_codes()

def get_component_types(session):
    component_types = session.doSomething('listComponentTypes', 'GET', {'filterMap': {'project': 'S', 'state': 'active'}})
    filtered_types  = []
    for ct in component_types:
        if 'TEST1' in ct['code']:
            continue
        localname_property, rfid_property = False, False
        properties = ct.get('properties', [])
        if not properties:
            continue
        for p in properties:
            if any(kw in p.get('code', '') for kw in _LOCALNAME_CODES):
                localname_property = True
            if any(kw in p.get('code', '') for kw in _RFID_CODES):
                rfid_property = True
        if localname_property and rfid_property:
            filtered_types.append(ct)
    return filtered_types

def get_input(prompt):
    print(prompt.strip() + ' ')
    while True:
        response = input()
        if response.strip() == '':
            continue
        break
    return response

def upload_RFID_to_component(port):
    s = ITkPDSession()
    s.authenticate()
    component_types = get_component_types(s)
    print('*** UPLOAD RFID TO COMPONENT ***')
    print('This script only works for the following component types:')
    for ct in component_types:
        print('    -- %s (%s)' % (ct['name'], ct['code']))
    print('Acceptable identifiers include a component codes, serial numbers, alternative identifiers, or local object names.')
    while True:
        identifier = get_input('Enter an identifier:')
        component  = get_component(s, identifier, component_types)
        if not component:
            print('Could not find the above component (deleted components are excluded) - please try again.')
            continue
        print('Found the following component:')
        print('    SN                : %s' % component.get('serialNumber'))
        print('    Alternative ID    : %s' % component.get('alternativeIdentifier'))
        print('    Component type    : %s' % component.get('componentType', {}).get('name') if component.get('componentType', {}) is not None else None)
        print('    Local object name : %s' % [p['value'] for p in component['properties'] if p['code'] in _LOCALNAME_CODES][0])
        print('    Stage             : %s' % component.get('currentStage', {}).get('name') if component.get('currentStage', {}) is not None else None)
        print('    Current location  : %s' % component.get('currentLocation', {}).get('name') if component.get('currentLocation') is not None else None)
        if get_input('Is this the component you are looking for? [y/n]:') == 'y':
            rfid_code    = None
            current_rfid = None
            for p in component['properties']:
                if p['code'] in _RFID_CODES:
                    rfid_code    = p['code']
                    current_rfid = p['value']
            if current_rfid is not None:
                print('The component already has an RFID uploaded: %s' % current_rfid)
                if get_input('Do you want to *update* the RFID? [y/n]:') != 'y':
                    print('Continuing.')
                    continue
            while True:
                print('Please scan the RFID.')
                data = read_RFID(port)
                if data:
                    break
                print('Could not read the RFID - please try again.')
            rfid = data['EPC ID'].upper()
            print('The following RFID was found: %s' % rfid)
            if get_input('Do you want to upload this RFID? [y/n]') == 'y':
                try:
                    s.doSomething('setComponentProperty', 'POST', {'component': component['code'], 'code': rfid_code, 'value': rfid})
                    print('Uploaded successfully.')
                except RequestException:
                    print('Could not upload the RFID, RequestException raised.')
        if get_input('Do you want to upload another RFID? [y/n]:') == 'y':
            continue
        break
    print('Finished.')

if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser(description = 'Upload an RFID to a component.', epilog = 'Once ready to read an RFID, hold down the channel button of the ThingMagic reader and press the antenna to the RFID chip. If you cannot open the port, trying running the script with \'sudo\'.')
        parser.add_argument('-p', dest = 'port', type = str, default = '/dev/ttyACM0', help = 'Path to the serial port the ThingMagic reader is connected to (e.g., /dev/ttyACM0 on Linux).')
        args = parser.parse_args()
        sys.exit(upload_RFID_to_component(args.port))
    except KeyboardInterrupt:
        print('\nExiting gracefully.')
