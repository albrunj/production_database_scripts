#!/bin/env python3
import copy
import getpass
import json
import os
import sys
import time

if sys.version_info < (3, 0):
    print("Python 2 no longer supported")
    sys.exit(1)

try:
    # Installed by default on lxplus
    import requests
except:
    print("Please install the requests module,")
    print("the equivalent of one of the following:")
    print("  pip install requests")
    print("  yum install python-requests")
    sys.exit(1)

try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except ImportError:
    MultipartEncoder = None

from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

# Shouldn't be used outside this module
_AUTH_URL = 'https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/'
_SITE_URL = 'https://itkpd-test.unicorncollege.cz/'
_BIN_URL  = 'https://itkpd-test.unicorncollege.cz/uu-app-binarystore/'
_AUDIENCE = 'https://itkpd-test.unicorncollege.cz'

# Define an exception specific to this file so that we may catch them (if we wish)
class dbAccessError(Exception):
    def __init__(self, message, *args, **kwargs):
        self.full_info = kwargs.pop("full_info", None)
        self.code = kwargs.pop("code", None)
        super(dbAccessError, self).__init__(*args, **kwargs)
        self.message = message
    def __str__(self):
        return self.message

# Recommended page sizes when fetching data (for pagination)
_UUCMD_LIST_PAGE_SIZE = {'listInstitutions': 3000, 'listComponents': 3000, 'listMyComponents': 3000, 'listTestRunsByTestType': 3000}
_UUCMD_BULK_PAGE_SIZE = {'getComponentBulk': {'page_size': 100, 'key': 'component'}, 'getTestRunBulk': {'page_size': 100, 'key': 'testRun'}}

class PageData(object):

    __slots__ = ['parent', 'kwargs', 'data', 'page_index', 'page_size', 'last_size', 'key', 'cache', 'cache_data']

    def __init__(self, parent = None, kwargs = {}, cache = False):
        super(PageData, self).__init__()
        # Do we want this type checking? Can it be made more general?
        if not isinstance(parent, ITkPDSession):
            raise TypeError('Parent must be of type \'ITkPDSession\': type(parent) = %s' % type(parent))
        action = kwargs.get('action', None)
        if action is None:
            raise KeyError('Action cannot be None.')
        if action not in list(_UUCMD_LIST_PAGE_SIZE.keys()) + list(_UUCMD_BULK_PAGE_SIZE.keys()):
            raise KeyError('Unknown action: %s' % action)
        self.parent     = parent
        self.kwargs     = kwargs
        self.data       = None
        self.page_index = -1
        self.page_size  = -1
        self.last_size  = int(1e9)
        self.key        = None
        self.cache      = cache
        self.cache_data = {}
        self.__setDefaults()

    def __setDefaults(self):
        action = self.kwargs['action']
        if action in list(_UUCMD_LIST_PAGE_SIZE.keys()) + list(_UUCMD_BULK_PAGE_SIZE.keys()):
            self.page_size  = self.kwargs['data'].get('pageInfo', {}).get('pageSize', None)
            self.page_index = self.kwargs['data'].get('pageInfo', {}).get('pageIndex', 0)
            self.last_size  = int(1e9)
            if self.page_size is None:
                if action in _UUCMD_LIST_PAGE_SIZE.keys():
                    self.page_size = _UUCMD_LIST_PAGE_SIZE[action]
                else:
                    self.page_size = _UUCMD_BULK_PAGE_SIZE[action]['page_size']
            if action in _UUCMD_BULK_PAGE_SIZE.keys():
                self.key = _UUCMD_BULK_PAGE_SIZE[action]['key']
        else:
            raise dbAccessError('Shouldn\'t arrive here!')

    def __getKwargs(self, i):
        action = self.kwargs['action']
        kwargs = copy.deepcopy(self.kwargs)
        if action in _UUCMD_LIST_PAGE_SIZE.keys():
            kwargs['data'].update({'pageInfo': {'pageSize': self.page_size, 'pageIndex': i}})
        elif action in _UUCMD_BULK_PAGE_SIZE.keys():
            kwargs['data'][self.key] = self.kwargs['data'][self.key][(self.page_size * i):(self.page_size * (i + 1))]
            if 'pageInfo' in kwargs['data'].keys():
                del kwargs['data']['pageInfo']
        else:
            raise dbAccessError('Shouldn\'t arrive here!')
        # Set return_paginated to False, as now we actually want to send the requests
        kwargs['return_paginated'] = False
        return kwargs

    def __call__(self):
        return self.data

    def __getitem__(self, i):
        self.page_index = i
        if self.cache and i in self.cache_dict.keys():
            self.data = self.cache_data[i]
        else:
            self.data = self.parent.doSomething(**self.__getKwargs(i))
            if self.cache:
                self.cache_data[i] = self.data
        self.last_size = len(self.data)
        return self.data

    def __iter__(self):
        self.__setDefaults()
        return self

    def __next__(self):
        if self.last_size < self.page_size:
            raise StopIteration
        data = self[self.page_index]
        self.page_index += 1
        return data

    def __len__(self):
        return len(self.data)

    def all(self):
        data = []
        for page in self:
            data += page
        return data

    next = __next__

# Define a class for wrapping up authentication/doSomething commands but in a single requests session
class ITkPDSession(requests.Session):

    __slots__ = ['enable_printing', 'dbAccessString', 'token', 'debug']

    def __init__(self, enable_printing = True, debug = False):
        super(ITkPDSession, self).__init__()
        self.enable_printing = enable_printing
        self.dbAccessString = '\033[1m' + '\033[97m' + 'dbAccess:' + '\033[0m' + ' '
        # Token
        self.token       = {'token': None, 'issued_at': -1, 'expires_at': -1, 'expires_in': -1}
        # Debug mode is only printing POST requests, not actually sending them
        self.debug = debug

    def __print(self, string, style = 'h', force = False):
        if self.enable_printing or force:
            if style in ['h', 'header']:
                print(self.dbAccessString + string)
            elif style in ['p', 'pretty']:
                pp.pprint(string)
            else:
                print(string)

    def getTokenFromEnv(self, check_expiry = False):
        ITK_DB_AUTH = os.getenv('ITK_DB_AUTH', None)
        if ITK_DB_AUTH is None:
            return False
        self.__print('Token already exists in shell environment.')
        if check_expiry:
            ITK_DB_AUTH_EXPIRES_AT = os.getenv('ITK_DB_AUTH_EXPIRES_AT', None)
            if ITK_DB_AUTH_EXPIRES_AT is None:
                self.__print('WARNING : Environment variable \'ITK_DB_AUTH_EXPIRES_AT\' has not been set, token from shell may have expired.')
            elif time.time() > float(ITK_DB_AUTH_EXPIRES_AT):
                self.__print('WARNING : Token in shell environment has expired, requiring user input.')
                return False
        self.setToken(ITK_DB_AUTH)
        return True

    def authenticate(self, accessCode1 = None, accessCode2 = None, check_expired=True):
        # Check if token expired
        if check_expired: # Don't authenticate if have a valid token
            if not self.checkTokenExpired(): return

        # Clean-up old token
        self.setToken(None)

        # Get new token
        self.__print('Getting token.')
        if not self.getTokenFromEnv():
            data = {'grant_type': 'password'}
            if accessCode1 is None or accessCode2 is None:
                data['accessCode1'] = getpass.getpass(self.dbAccessString + 'Enter AccessCode 1:')
                data['accessCode2'] = getpass.getpass(self.dbAccessString + 'Enter AccessCode 2:')
            else:
                data['accessCode1'], data['accessCode2'] = accessCode1, accessCode2
            data['scope'] = "openid %s" % _AUDIENCE
            data = to_bytes(json.dumps(data))
            self.__print('Sending credentials to get a token.')
            issued_at = time.time()
            token = self.doSomething(action = 'grantToken', method = 'POST', data = data, url = _AUTH_URL)
            self.setToken(token = token.get('id_token', None), issued_at = issued_at, expires_at = issued_at + token.get('expires_in', -1), expires_in = token.get('expires_in', -1))
        return self.token['token']

    def setToken(self, token, issued_at = -1., expires_at = -1., expires_in = -1.):
        self.token = dict(token = token, issued_at = float(issued_at), expires_at = float(expires_at), expires_in = float(expires_in))
        if token==None:
            self.headers.pop('Authorization', None)
        else:
            self.headers.update({'Authorization': 'Bearer ' + self.token['token']})

    def checkTokenExpired(self):
        """ Returns true if token is 60 seconds from expiry """
        return self.token['expires_at']<time.time()+60

    def download(self, code, savepath, overwrite = False):
        response = self.doSomething(action = 'getBinaryData', method = 'GET', data = {'code': code}, url = _BIN_URL, return_response = True)
        if os.path.exists(savepath):
            if overwrite:
                self.__print('Savepath \'%s\' already exists, but it will be overwritten.' % savepath)
            else:
                self.__print('WARNING : Savepath \'%s\' already exists, and it will NOT be overwritten (unless you set \'overwrite\' = True).' % savepath)
                return
        with open(savepath, 'wb') as file:
            file.write(response.content)

    def doSomething(self, action, method, data = None, url = _SITE_URL, return_response = False, return_paginated = False, return_error_map = False):
        kwargs = dict(action = action, method = method, data = data, url = url, return_response = return_response, return_paginated = return_paginated, return_error_map = return_error_map)
        # Check if we should return paginated data at the very start:
        if return_paginated and action in list(_UUCMD_LIST_PAGE_SIZE.keys()) + list(_UUCMD_BULK_PAGE_SIZE.keys()):
            return PageData(parent = self, kwargs = kwargs)
        # Else it's business as usual:
        if data is None:
            data = {}
        if MultipartEncoder is not None and isinstance(data, MultipartEncoder):
            self.headers.update({'Content-Type' : data.content_type})
        else:
            self.headers.update({'Content-Type' : 'application/json'})
            if not isinstance(data, bytes):
                data = to_bytes(json.dumps(data))
        # If in debug mode, just print the request
        if self.debug:
            self.__print('DEBUG : Sending data to url: %s' % (url + action), force = True)
            self.__print('DEBUG : Data:', force = True)
            self.__print(data, 'p', force = True)
            self.__print('DEBUG : Please note that this data was not actually sent.', force = True)
            return {}
        # Else, actually send it
        if method == 'GET':
            response = self.get(url = url + action, data = data)
        elif method == 'POST':
            response = self.post(url = url + action, data = data)
        else:
            raise dbAccessError('Unknown method: %s' % method)
        if response.status_code != 200:
            try:
                uuAppErrorMap = response.json()['uuAppErrorMap']
            except (KeyError, ValueError):
                uuAppErrorMap = None
            # Re-enable printing to console for error details
            self.__print('ERROR : Bad status code: %s' % response.status_code, force = True)
            self.__print('Request headers:', force = True)
            self.__print(response.headers, 'p', force = True)
            try:
                uuAppErrorMap = response.json()['uuAppErrorMap']
                self.__print('ITkPD uAppErrorMap:', force = True)
                self.__print(uuAppErrorMap, 'p', force = True)
            except (KeyError, ValueError):
                self.__print('WARNING : No uuAppErrorMap available.', force = True)
                self.__print('Response text:', force = True)
                self.__print(response.text, force = True)
            response.raise_for_status()
        # If we just want to return the raw requests response:
        if return_response:
            return response
        # In most other cases, we can anticipate the data we want to extract from the response:
        else:
            try:
                dataOut = response.json()
            except ValueError:
                self.__print('WARNING : No json could be decoded -- returning text.', force = True)
                dataOut = response.text
        if 'pageItemList' in dataOut:
            return_value = dataOut['pageItemList']
        elif 'itemList' in dataOut:
            return_value = dataOut['itemList']
        elif 'testRunList' in dataOut:
            return_value = dataOut['testRunList']
        elif 'dtoSample' in dataOut:
            return_value = dataOut['dtoSample']
        else:
            return_value = dataOut
        # Include the error map, if desired (return as a tuple in these cases)
        if return_error_map:
            if 'uuAppErrorMap' in dataOut:
                return_value = (return_value, dataOut['uuAppErrorMap'])
            else:
                return_value = (return_value, {})
        return return_value

verbose = False

token = None

testing = False
if os.getenv("TEST_OVERRIDE"):
    testing = True

def setupConnection():
    global token

    print("Setup connection")

    token = authenticate()

def to_bytes(s):
    """Reinterpret (utf-8 encoded) string to bytes for network transfer"""
    return bytes(s, 'utf-8')

def myprint(s, error = False):
    if not error:
        print(s)
    else:
        sys.stderr.write(s + '\n')

def authenticate(accessCode1 = None, accessCode2 = None):
    sys.stderr.write("Getting token\n")
    # post
    # Everything is json header

    a = {"grant_type": "password"}

    if accessCode1 is not None and accessCode2 is not None:
        a["accessCode1"] = accessCode1
        a["accessCode2"] = accessCode2
    else:
        a["accessCode1"] = getpass.getpass("AccessCode1: ")
        a["accessCode2"] = getpass.getpass("AccessCode2: ")

    a['scope'] = "openid %s" % _AUDIENCE

    a = to_bytes(json.dumps(a))

    sys.stderr.write("Sending credentials to get a token\n")

    result = doSomething("grantToken", a, url = _AUTH_URL)

    # print("Authenticate result:", result)

    id_token = result["id_token"]

    return id_token

def listComponentTypes():
    printGetList("listComponentTypes?project=S",
                 output = "{name} ({code})")

def doMultiSomething(url, paramdata = None, method = None,
                     headers = None,
                     attachments = None):

    if verbose:
        print("Multi-part request to %s" % url)
        print("Send data: %s" % paramdata)
        print("Send headers: %s" % headers)
        print("method: POST")

    # print paramdata
    r = requests.post(url, data = paramdata, headers = headers,
                      files = attachments)

    if r.status_code in [500, 401]:
        print("Presumed auth failure")
        print(r.json())
        return None

    if r.status_code != 200:
        print(r)
        print(r.status_code)
        print(r.headers)
        print(r.text)
        r.raise_for_status()

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

# Passed the uuAppErrorMap part of the message response
def decodeError(message, code):
    if "uu-app-server/internalServerError" in message:
        # Eg authentication problem "Signature verification raised"
        message = message["uu-app-server/internalServerError"]
        message = message["message"]
        print("Server responded with error message (code %d):" % code)
        myprint("\t%s" % message)
        return

    if "uu-appg01/authentication/invalidCredentials" in message:
        sys.stderr.write("Server reported invalid credentials (code %d):\n" % code)
        return

    if "uu-oidc-main/notAuthenticated" in message:
        # Returned from the authentication attempt
        message = message["uu-oidc-main/notAuthenticated"]
        message = message["message"]
        sys.stderr.write("Server responded with error message (code %d):\n" % code)
        myprint("\t%s" % message, error=True)
        return

    found = False

    for k in message.keys():
        if "cern-itkpd-main" in k:
            if "componentTypeDaoGetByCodeFailed" in k:
                found = True
                print("Either component type is invalid, or nothing found")
                continue
            elif "invalidDtoIn" in k:
                print("Decoding error message in %s" % k)
                found = True
        else:
            continue

        info = message[k]

        if "paramMap" in info:
            paramInfo = info["paramMap"]
            if "missingKeyMap" in paramInfo:
                for (k, v) in paramInfo["missingKeyMap"].items():
                    if len(list(v.keys())) == 1:
                        reason = v[list(v.keys())[0]]
                    else:
                        myprint("%s" % v.keys())
                        reason = v

                    if "$" in k:
                        # Seem to have $. in front
                        param_name = k[2:]
                    else:
                        param_name = k
                    myprint("Key '%s' missing: %s" % (param_name, reason))
            # There's probably also a invalidValueKeyMap which might be useful
        else:
            myprint(str(info))

    if not found:
        myprint("Unknown error message: %s" % str(message))

def doRequest(url, data = None, headers = None, method = None):
    if method == "post" or method == "POST" or (method is None and data is not None):
        method = "POST"
    else:
        method = "GET"

    if verbose:
        print("Request to %s" % url)
        print("Send data %s" % data)
        print("Send headers %s" % headers)
        print("method %s" % method)

    if method == "POST":
        # print("Sending post")
        r = requests.post(url, data = data,
                          headers = headers)
    else:
        # print("Sending get")
        r = requests.get(url, data = data,
                         headers = headers)

    if r.status_code == 401:
        j = r.json()
        if "uuAppErrorMap" in j and len(j["uuAppErrorMap"]) > 0:
            if "uu-oidc/invalidToken" in j["uuAppErrorMap"]:
                global token
                print("Auth failure, need a new token!")
                token = None
                raise dbAccessError("Auth failure, token out of date")

    if r.status_code != 200:
        try:
            message = r.json()["uuAppErrorMap"]

            if verbose:
                print(r.status_code)
                print(r.headers)
                myprint("errormap: %s" % str(message))
            decodeError(message, r.status_code)
            raise dbAccessError("Error from DB", full_info = message, code = r.status_code)
        except KeyError as a:
            myprint("Failed to decode error: %s" % str(a))

            # print(r)
            print(r.status_code)
            print(r.headers)
            print(r.text)
            raise dbAccessError("Bad status code")
        except ValueError as a:
            myprint("Failed to decode error as json: %s" % str(a))

            # print(r)
            print(r.status_code)
            print(r.headers)
            print(r.text)
            raise dbAccessError("Bad status code")

    if "content-type" in r.headers:
        # Expect "application/json; charset=UTF-8"
        ct = r.headers["content-type"]
        if (ct.split(";")[0].strip()) != "application/json":
            myprint("Received unexpected content type: %s" % ct)
    else:
        print(r.headers)

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

def doSomething(action, data = None, url = None, method = None,
                attachments = None):
    if testing:
        return doSomethingTesting(action, data, url, method, attachments)

    if token is None and url is None:
        setupConnection()
        if token is None:
            print("Authenticate failed")
            return

    if url is None:
        baseName = _SITE_URL
    else:
        baseName = url

    baseName += action

    if attachments is not None:
        # No encoding of data, as this is passed as k,v pairs
        headers = {"Authorization": "Bearer %s" % token}
        return doMultiSomething(baseName, paramdata = data,
                                headers = headers,
                                method = method, attachments = attachments)

    if data is not None:
        if type(data) is bytes:
            reqData = data
        else:
            reqData = to_bytes(json.dumps(data))
        if url is None: # Default
            pass # print("data is: ", reqData)
    else:
        reqData = None

    headers = {'Content-Type' : 'application/json'}
    headers.update({"Accept-Encoding": "gzip, deflate"})
    # Header, token
    if token is not None:
        headers["Authorization"] = "Bearer %s" % token

    result = doRequest(baseName, data = reqData,
                       headers = headers, method = method)

    return result

def extractList(*args, **kw):
    "Extract data for a list of things (as json)"
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]

    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        myprint("Response not json: %s" % str(data))
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:
            #myprint(str(j))
            return j
    else:
        # Sublist
        l = j["pageItemList"]

    if output is None:
        # All data
        return l
    else:
        # Just one piece
        if type(output) is list:
            result = []
            for i in l:
                result.append(list(i[o] for o in output))
            return result
        else:
            return [i[output] for i in l]

def printItem(item, format):
    print(format.format(**item))

def printGetList(*args, **kw):
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]
    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        myprint("Response not json: %s" % data)
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:
            # print(str(j))
            l = [j]
    else:
        # Returned sublist
        l = j["pageItemList"]

    if verbose:
        myprint("%s" % l)

    if output is not None:
        for i in l:
            printItem(i, output)
    else:
        printList(l, "print_first" in kw)

# If output is short enough, can print on one line
def isShortDict(d):
    keys = list(d.keys())

    if "*" in keys: # Threshold bounds
        return True
    if "children" in keys and len(d["children"]) > 0:
        return False
    if "code" in keys and "name" in keys:
        return True
    if "properties" in keys and d["properties"] is not None:
        return False
    if "userIdentity" in keys:
        return True
    return False

simple_type_list = [bool, int, float, str]

def printDict(d, indentation=''):
    # First match common dicts
    keys = list(d.keys())

    if "*" in keys:
        # Threshold: {'*': {'max': None, 'nominal': None, 'min': None}
        print("%s\t*..." % indentation)
        return

    try:
        if "value" in keys:
            # Most things have these parameters
            out = ("%s%s (%s) = %s"
                   % (indentation, d["name"], d["code"], d["value"]))
            print(out)
            keys.remove("code")
            keys.remove("name")
            keys.remove("value")
        elif "userIdentity" in keys:
            out = ("%s%s %s (%s)" % (indentation,
                                     d["firstName"], d["lastName"],
                                     d["userIdentity"]))
            print(out)
            keys.remove("lastName")
            keys.remove("firstName")
            keys.remove("userIdentity")

            # NB We intentionally ignore middleName
        elif "componentType" in keys and "user" not in keys:
            # eg Children of component
            comp = d["componentType"]["code"]
            subtype = d["type"]["code"]
            comp_id = d["id"]
            out = ("%s%s/%s (%s)" % (indentation, comp, subtype, comp_id))
            print(out)

            keys.remove("componentType")
            keys.remove("type")
            keys.remove("id")

            # For brevity, we ignore state, component, properties
        elif "comment" in keys:
            # Ignore datetime/user here
            myprint("%s%s" % (indentation, d["comment"]))
            keys.remove("comment")
        elif "filename" in keys:
            # Ignore datetime/user here
            myprint("%s%s" % (indentation, d["filename"]))
            keys.remove("filename")
        else:
            # Most else have these parameters
            out = ("%s%s (%s)"
                  % (indentation, d["name"], d["code"]))
            print(out)
            keys.remove("code")
            keys.remove("name")

        # test-type schema
        if "valueType" in keys and d["dataType"] != "compound":
            myprint("%s  %s %s" % (indentation, d["valueType"], d["dataType"]))
            keys.remove("valueType")
            keys.remove("dataType")
        if "children" in keys:
            keys.remove("children")
            subdict = d["children"]
            if subdict != None:
                printList(subdict, False, indentation)

        if "properties" in keys:
            p = d["properties"]
            if p is None:
                pass
            else:
                # print("%sProperties:" % indentation)
                printList(p, False, indentation)
                keys.remove("properties")

        if "parameters" in keys:
            print("%sParameters:" % indentation)
            printList(d["parameters"], False, indentation)
            keys.remove("parameters")

        if "testTypes" in keys and d["testTypes"] is not None:
            print("%sTest types:" % indentation)
            printList(d["testTypes"], False, indentation)
            keys.remove("testTypes")

        if verbose:
            if len(keys) > 0:
                myprint("%s\t\t Skipped keys: %s" % (indentation, keys))

        return
    except TypeError:
        # eg attempt to index list with string
        if len(indentation) > 1:
            print("%s...Printing unknown dict" % indentation)
    except KeyError:
        # Mostly the lower-level dicts match above patterns
        if len(indentation) > 1:
            print("%s...Printing unknown dict" % indentation)

            if verbose:
                print("%s\t\t (all names: %s)" % (indentation, list(d.keys())))

    indentation += "\t"

    # Generic
    for k, v in d.items():
        if v is None:
            print("%s%s: null" % (indentation, k))
        elif type(v) in simple_type_list:
            print("%s%s: %s" % (indentation, k,v))
        elif type(v) is list:
            print("%s%s (%d)" % (indentation, k, len(v)))
            printList(v, False, indentation)
        elif type(v) is dict:
            subdict = v
            # Sometimes short enough for one line
            if isShortDict(v):
                # No-new line difficult with Python 2 and 3
                sys.stdout.write("%s%s:" % (indentation, k))
                printDict(v, " ")
            else:
                print("%s%s:" % (indentation, k))
                printDict(v, indentation+"\t")
        else:
            myprint("%s?Type: %s: %s" % (indentation, k, v))

def printList(l, print_first, indentation='', location=''):
    first = True

    startLine = indentation + "\t"

    for i in l:
        if len(indentation) == 0:
            print("%sitem" % indentation)
        elif verbose:
            print("%sList item" % indentation)
        if len(indentation) > 0 and verbose:
            print(str(i))
        if first:
            if print_first:
                myprint("%sFirst: %s" % (startLine, i))
            first = False

        if type(i) is dict:
            printDict(i, startLine)
        elif type(i) in simple_type_list:
            print("%s%s" % (startLine, i))
        else:
            myprint("%s Unexpected type in list %s" % (indentation, type(i)))
            if verbose:
                print(i)

# listComponentTypes()

def summary(project="S"):
    print(" ===== Institutes =====")
    inst_output = "{name} ({code})"

    printGetList("listInstitutions", method = "GET", output = inst_output)

    print(" ==== Strip component types =====")
    printGetList("listComponentTypes?project=%s" % project, method = "GET",
                 output = "{name} ({code})")
    # ({subprojects}) ({stages}) ({types})")

    # name, code
    #  Arrays: subprojects, stages, types

    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")

    print(" ==== Test types by component =====")
    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")
    for tc in type_codes:
        myprint("Test types for %s" % tc)
        printGetList("listTestTypes", {"project": project,
                                       "componentType": tc},
                     method = "GET", output = "  {name} ({code}) {state}")

# Produce some response without talking to DB
def doSomethingTesting(action, data = None, url = None, method = None,
                       attachments = None):
    if verbose:
        print("Testing request: %s" % action)
        print(" URL: %s" % url)
        print(" data: %s" % data)
        print(" method: %s" % method)
        print(" attachments: %s" % attachments)

    def encode(s):
        j = to_bytes(json.dumps(s))
        j = json.loads(j.decode("utf-8"))
        return j

    if action == "grantToken":
        return {'id_token': "1234567890abcdf"}
    if action == "listInstitutions":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
                {'code': 'UNIA', 'supervisor': u'First Second With\xe4t\xeda Last', 'name': u'Universit\xe4t A'}, {u'code': u'UNIB', u'supervisor': 'Other Name', 'name': 'University B'}
            ]})
    elif action == "listComponentTypes":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
                {'code': 'COMPA', 'name': u'Hybrid Type A'}, {u'code': u'COMPB', 'name': 'Module Type B'}
            ]})
    elif action == "listComponents":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
            {'code': 'HYBA', 'name': u'Hybrid A', 'trashed': False, 'institution': {'code': 'UNIA'}},
            {u'code': u'MODB', 'name': 'Module B', 'trashed': True, 'institution': {'code': 'UNIA'}}
            ]})

    raise dbAccessError("Action %s not known for testing" % action)
