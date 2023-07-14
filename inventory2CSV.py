#!/usr/bin/env python
import os
from datetime import datetime

def inventory2CSV(outfile, inventory, write = [], properties = [], tests = [], overwrite = False):
    if os.path.exists(outfile) and not overwrite:
        raise OSError('Path already exists and will NOT be overwritten: %s' % outfile)
    f = open(outfile, 'w')
    keys = write + [('PROP_' + p) for p in properties]
    for t in tests:
        keys.append('TEST_PASS_%s' % t)
        keys.append('TEST_FAIL_%s' % t)
    header = '#Generated on %s\n' % datetime.now().strftime('%Y/%m/%d-%H:%M:%S')
    header += '#' + ','.join(keys) + '\n'
    f.write(header)
    line = '{' + '!s},{'.join(keys) + '}\n'
    for page in inventory:
        for c in page:
            try:
                data = {}
                data['code']                  = c['code']
                data['alternativeIdentifier'] = c.get('alternativeIdentifier')
                data['assembled']             = c.get('assembled')
                data['childrenAssembled']     = all(cc['component'] for cc in c['children']) if c.get('children') is not None else None
                data['type']                  = c.get('type', {}).get('code') if c.get('type') is not None else None
                data['completed']             = c.get('completed')
                data['componentType']         = c.get('componentType', {}).get('code')
                data['cts']                   = c.get('cts')
                data['currentGrade']          = c.get('currentGrade')
                data['currentLocation']       = c.get('currentLocation', {}).get('code') if c.get('currentLocation', {}) is not None else None
                data['currentStage']          = c.get('currentStage', {}).get('code') if c.get('currentStage', {}) is not None else None
                data['dummy']                 = c.get('dummy')
                data['institution']           = c.get('institution', {}).get('code') if c.get('institution', {}) is not None else None
                data['project']               = c.get('project', {}).get('code')
                data['qaPassed']              = c.get('qaPassed')
                data['qaState']               = c.get('qaState')
                data['reusable']              = c.get('reusable')
                data['reworked']              = c.get('reworked')
                data['serialNumber']          = c.get('serialNumber')
                data['shipmentDestination']   = c.get('shipmentDestination', {}).get('code') if c.get('shipmentDestination', {}) is not None else None
                data['state']                 = c.get('state')
                data['subproject']            = c.get('subproject', {}).get('code')
                data['trashed']               = c.get('trashed')
                data['user']                  = str(c.get('user', {}).get('firstName')) + str(c.get('user', {}).get('lastName'))
                data.update({('TEST_PASS_%s' % t): 0 for t in tests})
                data.update({('TEST_FAIL_%s' % t): 0 for t in tests})

                if c.get('properties', []) is not None:
                    for p in c.get('properties', []):
                        data['PROP_%s' % p['code']] = p['value']
            except Exception as e:
                # Should only fail if component structure is off
                print('Error : exception raised: %s' % e)
                print('Error : offending component:\n%s\n' % c)
                continue

            for t in c.get('tests', []):
                for tt in t.get('testRuns', []):
                    key = 'TEST_' + ('PASS' if tt['passed'] else 'FAIL') + '_%s' % t['code']
                    if key not in list(data.keys()):
                        data[key] = 0
                    data[key] += 1
            for k in keys:
                if k not in list(data.keys()):
                    data[k] = None
            f.write(line.format(**data))
    f.close()

def getInventory(session, full = False, **kwargs):
    components = session.doSomething(action = 'listComponents', method = 'GET', data = kwargs, return_paginated = True)
    if full:
        print('Info : full == True, running getComponentBulk.')
        components = session.doSomething(action = 'getComponentBulk', method = 'GET', data = {'component': [c['code'] for c in components.all()]}, return_paginated = True)
    return components

def list2Upper(inlist):
    if inlist is None:
        return inlist
    else:
        return [i.upper() for i in inlist]

def main(session, args):
    kwargs =    dict(   project           = args.project,
                        componentType     = list2Upper(args.componentType),
                        type              = list2Upper(args.type),
                        currentStage      = list2Upper(args.currentStage),
                        currentLocation   = list2Upper(args.currentLocation),
                        institution       = list2Upper(args.institution),
                        assembled         = bool(args.assembled),
                        includeProperties = True
                    )
    write         = args.write if args.write is not None else []
    properties    = args.properties if args.properties is not None else []
    tests         = args.tests if args.tests is not None else []
    do_properties = (len(properties) > 0)
    do_tests      = (len(tests) > 0)
    if len(args.componentType) > 1 and do_properties:
        raise RuntimeError('Selected >1 component types and asked for properties - unlikely different types share the same properties.')
    if len(args.componentType) > 1 and do_tests:
        raise RuntimeError('Selected >1 component types and asked for tests - unlikely different types share the same tests.')
    # If we're writing properties or tests, fetch the component type so we know which properties/tests are available
    if do_properties or do_tests:
        component_type            = session.doSomething(action = 'getComponentTypeByCode', method = 'GET', data = {'project': kwargs['project'], 'code': kwargs['componentType'][0]})
        component_type_properties = [p['code'] for p in component_type.get('properties', [])]
        component_type_tests      = []
        for s in component_type.get('stages', []):
            if s.get('testTypes') is not None:
                for t in s.get('testTypes', []):
                    component_type_tests.append(t.get('testType', {}).get('code'))
        component_type_tests = list(set([t for t in component_type_tests if t is not None]))
    # If we want to add all properties:
    if '-1' in properties:
        properties = component_type_properties
    properties = sorted(list2Upper(properties))
    properties2 = []
    for p in properties:
        if p not in component_type_properties:
            print('Warning : property \'%s\' is not associated with component type \'%s\' - purging from list.' % (p, kwargs['componentType'][0]))
        else:
            properties2.append(p)
    properties = properties2
    # If we want to add all tests:
    if '-1' in tests:
        tests = component_type_tests
    tests = sorted(list2Upper(tests))
    tests2 = []
    for t in tests:
        if t not in component_type_tests:
            print('Warning : test \'%s\' is not associated with component type \'%s\' - purging from list.' % (t, kwargs['componentType'][0]))
        else:
            tests2.append(t)
    tests = tests2
    # Check if we need to fetch detailed info for each component
    full = False
    if any(op in write for op in ['childrenAssembed', 'qaPassed', 'qaState', 'shipmentDestination', 'user']) or tests:
        full = True

    #derek's update: remove any keys with None values
    #kwargskeys = list(kwargs.keys())
    #for k in kwargskeys:
    #    if kwargs[k] == None:
    #        del kwargs[k]

    inventory = getInventory(session, full, **kwargs)
    inventory2CSV(outfile = args.outfile, inventory = inventory, write = write, properties = properties, tests = tests, overwrite = True)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description = 'Script for dumping ITk Production Database inventory to local CSV')
    parser.add_argument('-p', '--project', dest = 'project', type = str, choices = ['S', 'P', 'CE', 'CM'], default = 'S', help = 'project code for the component type(s)')
    parser.add_argument('-c', '--componentType', dest = 'componentType', nargs = '*', type = str, required = True, help = 'list of component type code(s) to fetch')
    parser.add_argument('-t', '--type', dest = 'type', nargs = '*', type = str, help = 'list of subtype code(s) to fetch')
    parser.add_argument('-s', '--currentStage', dest = 'currentStage', nargs = '*', type = str, help = 'list of current stage code(s) to fetch')
    parser.add_argument('-l', '--currentLocation', dest = 'currentLocation', nargs = '*', type = str, help = 'list of current location code(s) to fetch')
    parser.add_argument('-i', '--institution', dest = 'institution', nargs = '*', type = str, help = 'list of institution code(s) to fetch')
    parser.add_argument('-a', '--assembled', dest = 'assembled', action = 'store_true', help = 'include only assembled components')
    write_options = [   'alternativeIdentifier', 'assembled', 'type', 'childrenAssembled', 'code', 'completed', 'componentType', 'cts', 'currentGrade', 'currentLocation', 'currentStage', 'dummy',
                        'institution', 'project', 'qaPassed', 'qaState', 'reusable', 'reworked', 'serialNumber', 'shipmentDestination', 'state', 'subproject', 'trashed', 'user' ]
    parser.add_argument('-w', '--write', dest = 'write', nargs = '*', choices = write_options, type = str, default = ['code'], help = 'general info to write out (excluding properties, serial numbers are ALWAYS included)')
    parser.add_argument('-pr', '--properties', dest = 'properties', nargs = '*', type = str, default = [], help = 'list of property code(s) to include in the outfile (-1 := write all properties)')
    parser.add_argument('-ts', '--tests', dest = 'tests', nargs = '*', type = str, default = [], help = 'list of test code(s) to include in the outfile (-1 := write all tests)')
    parser.add_argument('-o', '--outfile', dest = 'outfile', type = str, default = './components.csv', help = 'outfile name')
    args = parser.parse_args()

    from itk_pdb.dbAccess import ITkPDSession
    session = ITkPDSession()
    session.authenticate()

    main(session, args)
