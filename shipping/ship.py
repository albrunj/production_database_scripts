#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import copy
import os
import sys
from pprint import PrettyPrinter

from itk_pdb.identifiers import checkComponentCode
from itk_pdb.identifiers import checkSerialNumber
from requests.exceptions import RequestException
from tabulate import tabulate

pp = PrettyPrinter(indent = 1, width = 200)

try:
    input = raw_input
except NameError:
    pass

_USE_COLOURS = True

def info(s):
    if _USE_COLOURS:
        print('\033[1m\033[97mInfo\033[0m    : ' + s)
    else:
        print('Info    : ' + s)

def warn(s):
    if _USE_COLOURS:
        print('\033[1m\033[93mWarning\033[0m : ' + s)
    else:
        print('Warning : ' + s)

def error(s):
    if _USE_COLOURS:
        print('\033[1m\033[91mError\033[0m   : ' + s)
    else:
        print('Error   : ' + s)

def transpose(l):
    return list(map(list, zip(*l)))

def readFile(file, skip_bad_codes = False):
    with open(file) as f:
        lines = [l.strip() for l in f.readlines()]
    components = []
    for i, l in enumerate(lines):
        if (l == '') or l.startswith('#'):
            continue
        if not (checkComponentCode(l) or checkSerialNumber(l)):
            warn('Line number %s does not look like a ITkPD component code or ATLAS SN: \'%s\'' % (i, l))
            if skip_bad_codes:
                warn('Skipping line %s to avoid probable issues during API calls.' % i)
                continue
            else:
                warn('Unhandled line %s - will likely cause problems during API calls.' % i)
        components.append(l)
    return components

class Cancel(Exception):
    pass

class Skip(Exception):
    pass

class Back(Exception):
    pass

def notInChoices(response, choices):
    if isinstance(choices, list):
        if len(choices) > 0:
            if isinstance(choices[0], dict):
                return (response not in [c['code'] for c in choices])
            else:
                return (response not in choices)
        else:
            return True
    else:
        return False

def askForSomething(prompt, choices = -1, escape = ['print', 'cancel', 'skip', 'back'], lower = False, upper = False):
    possible_escape = ['$quit', '$print', '$cancel', '$skip', '$back']
    escape += ['quit']
    info(prompt)
    while True:
        response = input().strip()
        lowered_response = response.lower()
        if lower:
            response = response.lower()
        elif upper:
            response = response.upper()
        if response == '':
            continue
        elif (lowered_response in possible_escape) and (lowered_response[1:] not in escape):
            info('Escape \'%s\' not supported here, please try again:' % lowered_response)
            continue
        elif lowered_response == '$quit':
            warn('Quitting.')
            sys.exit(0)
        elif lowered_response == '$print':
            if choices != -1:
                info('Printing choices:\n')
                if all(isinstance(c, dict) and 'code' in c.keys() and 'name' in c.keys() for c in choices):
                    print(tabulate(transpose([[c['name'].decode('utf-8') for c in choices], [c['code'].decode('utf-8') for c in choices]]), headers = ['Name', 'Code'], tablefmt = 'fancy_grid'))
                else:
                    for c in choices:
                        print('    ' + c)
                print('')
            else:
                info('No choices were specified.')
            info(prompt)
            continue
        elif lowered_response == '$cancel':
            warn('Cancelling.')
            raise Cancel
        elif lowered_response == '$skip':
            info('Skipping.')
            raise Skip
        elif lowered_response == '$back':
            info('Going back.')
            raise Back
        elif notInChoices(response, choices):
            del response
            del lowered_response
            info('Invalid input, please try again:')
            continue
        else:
            return response

def getYesOrNo(prompt, escape = []):
    yes = ['y', 'yes', '1', 'true']
    no  = ['n', 'no', '0', 'false']
    response = askForSomething(prompt, choices = yes + no, escape = ['print', 'cancel'] + escape, lower = True)
    if response in yes:
        return True
    else:
        return False

def getIndices(prompt):
    indices = askForSomething(prompt, choices = -1)
    indices = [i for i in indices.split() if i != '']
    indices = [i for i in indices.split(',') if i != '']
    indices = [i for i in indices.split('-') if i != '']
    indices2 = []
    for i in indices:
        if isinstance(i, list):
            indices2 += list(range(i[0], i[1] + 1))
        else:
            indices2.append(i)
    sorted(set(indices2))
    return indices2

def getComponents():
    components = []
    escape = ['skip', 'back']
    if getYesOrNo('Would you like to add components [y/n]?:', escape = escape):
        while True:
            file = askForSomething('Enter a filepath to an input list of component codes:')
            if not os.path.exists(file):
                warn('Filepath \'%s\' does not exist, please try again.' % file)
                continue
            if not os.path.isfile(file):
                warn('Filepath \'%s\' does not point to a file, please try again.' % file)
                continue
            tmp = readFile(file)
            info('Found components:\n')
            for c in tmp:
                print('    ' + c)
            print('')
            if getYesOrNo('Would you like to add these components to the shipment\'s inventory [y/n]?:', escape = escape):
                components += tmp
            if getYesOrNo('Would you like to add another file\'s content to the existing list [y/n]?:', escape = escape):
                continue
            else:
                break
    return components

def removeComponents(components):
    while True:
        info('Printing components:\n')
        print(tabulate(transpose([[i for i in range(len(components))], [c for c in components]]), headers = ['Index', 'Component Code / SN'], tablefmt = 'fancy_grid'))
        print('')
        indices = getIndices('Enter a list of comma- or space-separated indices (non-spaced hyphen denote ranges) for the components to be removed:')
        info('The following components will be removed:\n')
        print(tabulate(transpose([[i for i in indices], [c for c in components[indices]]]), headers = ['Index', 'Component Code / SN'], tablefmt = 'fancy_grid'))
        print('')
        if getYesOrNo('Confirm the removal [y/n]:'):
            components = [components[i] for i in range(len(components)) if i not in indices]
            break
        elif getYesOrNo('Would you like to remove a different subset of components [y/n]?:'):
            continue
        else:
            break
    return components

def performActions(data, actions, child = False):
    i = 0
    cached_data = [copy.deepcopy(data)] + len(actions) * [{}]
    while True:
        try:
            if i == len(actions):
                break
            if actions[i][0] is performActions:
                actions[i][0](data, child = child)
            else:
                actions[i][0](data)
            i += 1
            cached_data[i] = copy.deepcopy(data)
            continue
        except Skip:
            # Is the action skippable?
            if actions[i][1]:
                i +=1
                cached_data[i] = copy.deepcopy(data)
                continue
            else:
                warn('Action cannot be skipped.')
                continue
        except Back:
            if i == 0:
                if child:
                    raise Back
                else:
                    warn('Can\'t go back any further.')
                    continue
            else:
                while True:
                    data = cached_data[i]
                    i -= 1
                    if len(actions[i]) > 2 and actions[i][2]:
                        continue
                    else:
                        break
                continue
    return data

_ALLOWED_INSTITUTIONS = {}
def getShipmentParams(session, ask_for = ['name', 'sender', 'recipient', 'trackingNumber', 'shippingService', 'type', 'status'], child = False):
    data = {}
    if ('sender' in ask_for) or ('recipient' in ask_for):
        global _ALLOWED_INSTITUTIONS
        if _ALLOWED_INSTITUTIONS == {}:
            info('Fetching allowed institutions from the DB.')
            _ALLOWED_INSTITUTIONS = [{'code': i['code'], 'name': i['name']} for i in session.doSomething(action = 'listInstitutions', method = 'GET', data = {})]
    allowed_types = ['domestic', 'intraContinental', 'continental']
    allowed_statuses = ['prepared', 'inTransit', 'delivered', 'deliveredWithDamage', 'undelivered']
    actions = []
    if 'name' in ask_for:
        actions.append((lambda data: data.update({'name': askForSomething('Enter a name for the shipment:')}), False))
    if 'sender' in ask_for:
        actions.append((lambda data: data.update({'sender': askForSomething('Enter the sending institution code:', choices = _ALLOWED_INSTITUTIONS, upper = True)}), False))
    if 'recipient' in ask_for:
        actions.append((lambda data: data.update({'recipient': askForSomething('Enter the receiving institution code:', choices = _ALLOWED_INSTITUTIONS, upper = True)}), False))
    if 'trackingNumber' in ask_for:
        actions.append((lambda data: data.update({'trackingNumber': askForSomething('Enter the tracking number:')}), True))
    if 'shippingService' in ask_for:
        actions.append((lambda data: data.update({'shippingService': askForSomething('Enter the shipping service:')}), True))
    if 'type' in ask_for:
        actions.append((lambda data: data.update({'type': askForSomething('Enter the type of shipment:', choices = allowed_types)}), False))
    if 'status' in ask_for:
        actions.append((lambda data: data.update({'status': askForSomething('Enter the status of the shipment:', choices = allowed_statuses)}), False))
    performActions(data = data, actions = actions, child = child)
    return data

def getComments():
    comments = []
    escape = ['skip', 'back']
    if getYesOrNo('Would you like to add comments [y/n]?:', escape = escape):
        while True:
            comment = askForSomething('Enter a comment:')
            info('The following comment will be added:\n')
            print('    ' + comment)
            print('')
            if getYesOrNo('Would you like to add this comment [y/n]?:', escape = escape):
                comments.append(comment)
            if getYesOrNo('Would you like to add another comment [y/n]?:', escape = escape):
                continue
            else:
                break
    return comments

def registerShipment(session, data):
    escape = ['back']
    info('The following data will be used to register a shipment\n')
    pp.pprint(data)
    print('')
    if getYesOrNo('Do you want the above shipment to be registered [y/n]?:', escape = escape):
        try:
            session.doSomething(action = 'createShipment', method = 'POST', data = data)
        except RequestException as e:
            error('Request exception raised: %s' % e)
            error('Shipment could not be registered.')
            return
        info('Successfully registered shipment.')
    else:
        info('Registration aborted.')

def convertSNsToCompCodes(session, codes):
    converted_codes = []
    for c in codes:
        if checkSerialNumber(c):
            converted_codes.append(session.doSomething(action = 'getComponent', method = 'GET', data = {'component': c})['code'])
        elif checkComponentCode(c):
            converted_codes.append(c)
        else:
            warn('Identifier \'%s\' does not look like a serial number or a component code - will likely cause problems during API calls.' % c)
            converted_codes.append(c)
    return converted_codes

def createShipment(session, child = False):
    data = {'status': 'prepared'}
    actions = [
        (lambda data: data.update({'shipmentItems': getComponents()}), True),
        (lambda data: data.update(getShipmentParams(session = session, ask_for = ['name', 'sender', 'recipient', 'trackingNumber', 'shippingService', 'type'], child = True)), False),
        (lambda data: data.update({'comments': getComments()}), True),
        (lambda data: data.update({'shipmentItems': convertSNsToCompCodes(session = session, codes = data['shipmentItems'])}), False, True),
        (lambda data: registerShipment(session = session, data = data), False)
    ]
    info('Creating a shipment.')
    performActions(data = data, actions = actions, child = child)

def updateShipment(session, child = False):
    print('This does nothing at the moment, returning!')

def listMyShipments(session, child = False):
    print('This does nothing at the moment, returning!')

def main(session):
    print('')
    print('===================')
    print('===== ship.py =====')
    print('===================')
    print('')
    info('When requesting input, type \'$quit\' to quit, \'$print\' to print available options, \'$cancel\' to cancel an action, \'$skip\' to skip an action (if allowed), and \'$back\' to go back.')
    menu = {'0': createShipment, '1': updateShipment, '2': listMyShipments}
    while True:
        try:
            info('Printing menu:\n')
            print(tabulate(transpose([[i for i in sorted(menu.keys())], [menu[i].__name__ for i in sorted(menu.keys())]]), headers = ['Index', 'Command'], tablefmt = 'fancy_grid'))
            print('')
            action = askForSomething('Please enter an integer from the above menu options:', choices = sorted(menu.keys()), escape = ['print', 'cancel'])
            menu[action](session = session, child = False)
            info('Action completed.')
            if getYesOrNo('Would you like to perform another action [y/n]?:'):
                continue
            else:
                break
        except Cancel:
            continue
    info('All done!')
    sys.exit(0)

if __name__ == '__main__':
    from itk_pdb.dbAccess import ITkPDSession
    session = ITkPDSession()
    session.authenticate()
    try:
        sys.exit(main(session))
    except KeyboardInterrupt:
        print('')
        error('Keyboard interrupt - exiting.')
        sys.exit(1)
    except RequestException as e:
        print('')
        error('Unhandled request exception raised: %s' % e)
        error('Exiting.')
        sys.exit(1)
