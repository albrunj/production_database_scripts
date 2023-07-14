#!/usr/bin/env python3
"""Read an excel/CSV file and creates as many shipments as rows.

Columns are

name: shipment name
sender: code of the institution
recipient: code of the institutiom
trackingNumber: optional
shippingService; optional
type: (domestic | intraContinental | continental)
status: ["prepared", "inTransit", "delivered", "deliveredIncomplete", "deliveredWithDamage", "undelivered"]
shipmentItems: ';'-separated list of SN
comments: ';'-separated list of comments.
attachments: ';'-separated list of attachment uris. use file:path_to_file for files and https:the_link for links

In a CSV file, it might be wise to surround shipItems, comments and attachments by "" if there is more than one.

It will produce a text file with one line per shipmet made containing
the  shipment id and the attachment ids.

"""
if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys
from pathlib import Path
import json
import csv
import mimetypes
from argparse import ArgumentParser
from urllib.parse import urlparse

# WE use openpyxl to read XLSX files
from openpyxl.utils.exceptions import InvalidFileException
import openpyxl as XL

import difflib

from requests.exceptions import RequestException
from itk_pdb.dbAccess import ITkPDSession, dbAccessError
import itk_pdb.dbAccess as dbAccess

from shipping.ship import convertSNsToCompCodes

STATUS = ["prepared", "inTransit", "delivered", "deliveredIncomplete", "deliveredWithDamage", "undelivered"]
TYPES = ["domestic", "intraContinental", "continental"]


def get_word_in_list(word, the_list):
    """Return the closest word in the list.

    Args:
    ----
        word: The word
        the_list: the list of words

    Returns
    -------
        [type]: the selection. None if none is valid.

    """
    for w in the_list:
        if word == w.lower():
            return w

    w = difflib.get_close_matches(word, the_list)
    if len(w):
        return w[0]
    else:
        return None


def check_values_in_list(data, key, default_value, the_list):
    """Check that data[key] in an allowed value as for the_list."""
    if key not in data or data[key] is None:
        data[key] = default_value

    else:
        if data[key] not in the_list:
            # Check if we mis-spelled the value
            word = get_word_in_list(data[key], TYPES)
            if word is not None:
                data[key] = word

            else:
                print("wrong value {}. Allowed values {}".format(data[key], the_list))
                raise ValueError

    return data


def main(session, sheet, ofile):
    """Read the XSLX or CSV file and create one shipment per row.

    Args:
    ----
        session: itkpd session object
        sheet: XLSX sheet or CSV reader

    Returns
    -------
        [int]: 0 if ok, !=0 otherwise

    """
    header = {}
    shipments = []
    errors = 0
    for i, row in enumerate(sheet):
        if i == 0:
            # Find the headers and make teh mapping with columns
            for j, item in enumerate(row):
                try:
                    header[item.value] = j
                except AttributeError:
                    header[item] = j

            # Sanity checks
            for key in ['name', 'sender', 'recipient', 'shipmentItems']:
                if key not in header:
                    return -1

            continue

        # Real data comes here
        data = {}
        try:
            values = [x.value for x in row]
        except AttributeError:
            values = [x if len(x) else None for x in row]

        # Get common data
        for key in ['name', 'sender', 'recipient', 'type', 'status']:
            if key in header:
                data[key] = values[header[key]]

        # List of items
        items = []
        list_of_sn = values[header['shipmentItems']]
        for sn in list_of_sn.split(';'):
            items.append(sn.strip())

        if len(items):
            data['shipmentItems'] = convertSNsToCompCodes(session, items)

        else:
            print("Shipment from {} to {} with no items".format(data['sender'], data['recipient']))
            errors += 1
            continue

        # list of comments
        comments = []
        list_of_comments = values[header['comments']]
        for cmmt in list_of_comments.split(';'):
            comments.append(cmmt.strip())

        if len(comments):
            data['comments'] = comments

        # list of attachments
        attachments = []
        if 'attachments' in header:
            list_of_attachments = values[header['attachments']]
            if list_of_attachments is not None:
                for att in list_of_attachments.split(';'):
                    attachments.append(att)

            if len(attachments):
                data['attachments'] = attachments

        # Check list
        try:
            data = check_values_in_list(data, 'type', 'continental', TYPES)
            data = check_values_in_list(data, 'status', 'prepared', STATUS)

        except ValueError:
            errors += 1
            continue

        shipments.append(data)

    if errors:
        return -1

    # Do the shipments
    nerror = 0
    for S in shipments:
        # Prepare the attachmetns and remove them from the
        # shipment creation payload.
        attachments = []
        if 'attachments' in S:
            for att in S['attachments']:
                # att is a uri. parse it.
                rc = urlparse(att)
                path = Path(rc.path)
                attd = {}
                attd['title'] = path.name
                if rc.scheme == 'file':
                    if path.exists():
                        attd['type'] = 'file'
                        attd['data'] = open(path.as_posix(), 'rb')
                        attachments.append(attd)

                elif rc.scheme == "http" or rc.scheme == "https":
                    if len(rc.path) == 0:
                        attd['title'] = rc.netloc

                    attd['type'] = 'link'
                    attd['url'] = att
                    attd['data'] = att
                    attachments.append(attd)

            del S['attachments']

        try:
            resp = session.doSomething(action='createShipment',
                                       method='POST',
                                       data=S, return_response=True)

            if resp.status_code != 200:
                print("Could not create shipment to {} with {} items".format(S['recipient'], len(S['shipmentItems'])))
                nerror += 1
                continue

            out = json.loads(resp.content)
            print("Shipment {} to {} with {} items is {}".format(out['id'],
                                                                 out['recipient']['code'],
                                                                 len(out['shipmentItems']),
                                                                 out['status']))
            ofile.write("{}".format(out['id']))

            # Shipment created.
            # Now create the attachments for the  shipment
            for attachment in attachments:
                attachment['shipment'] = out['id']
                att_data = attachment['data']
                att_name = attachment['title']
                att_type = mimetypes.guess_type(att_name)
                del attachment['data']
                res = dbAccess.doSomething("createShipmentAttachment",
                                           attachment,
                                           attachments={"data": (att_name, att_data, att_type[0])})
                if res is not None:
                    if 'type' in res:
                        the_type = res['type']
                        the_name = res['title']
                    else:
                        the_type = "file"
                        the_name = res['name']

                    if 'id' in res:
                        ofile.write(" {}".format(res['id']))

                    print("...Added attachment [{}] {}".format(the_type, the_name))
                else:
                    print("+++ Something went wrong when creating the attachment")

            ofile.write('\n')
        except dbAccessError as e:
            print("***Error talking to DB: {}".format(e))
            nerror += 1

        except RequestException as e:
            print('*** Request exception raised: %s' % e)
            print('*** Shipment could not be registered.')
            print(S)
            nerror += 1

    return nerror


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('files', nargs='*', help="Input files")
    parser.add_argument('--status', type=str, default=None)
    parser.add_argument("--out", action="store", type=str,
                        dest="out_file", default="shipments.txt",
                        help="Output file")

    options = parser.parse_args()

    try:
        fname = options.files[0]

    except IndexError:
        print("I need an input file.")
        sys.exit(1)

    fpath = Path(fname)
    if not fpath.exists():
        print("Input file does not exist.")
        sys.exit(1)

    # Try with CSV
    if fpath.suffix.lower() == ".csv":
        try:
            ifile = open(fname, "r", newline='')
            ws = csv.reader(ifile)

        except Exception as ee:
            print("Could not open input file: ", fname)
            print(ee.message)
            sys.exit(1)

    # It must be excel
    else:
        try:
            wb = XL.load_workbook(fname)
            ws = wb.active

        except InvalidFileException as ee:
            print("Could not open input file: ", fname)
            print(ee.message)
            sys.exit(1)

    # Initialize the session in the ITk PDB
    session = ITkPDSession()
    session.authenticate()
    dbAccess.token = session.token['token']
    try:
        ofile = open(options.out_file, 'w')
        rc = main(session, ws, ofile)
        ofile.close()
        sys.exit(rc)

    except KeyboardInterrupt:
        print('')
        print('Keyboard interrupt - exiting.')
        sys.exit(1)
    except RequestException as e:
        print('')
        print('Unhandled request exception raised: %s' % e)
        print('Exiting.')
        sys.exit(1)
