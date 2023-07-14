#!/usr/bin/python
import time

import itkdb

#from __path__ import updatePath
#updatePath()




# VF, 2021-05-01: Will use a global variable to indicate the state of DB connection affairs
bad_connection = False # original goodness

def get_code(c,SN):
    global bad_connection
    try:
        Resp = c.get('getComponent', json = {'component':SN})
    except Exception as e:
        print("object not found: " + SN )
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_code>")
            bad_connection = True

    objCode = Resp['code']

    return objCode


def get_testdata(c,testID):
    global bad_connection
    try:
        resp = c.get('getTestRun',json ={'testRun':testID})
    except Exception as e:
        resp = None
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_testdata>")
            bad_connection = True

    return resp

def get_testruns_dict(c, objCode):
    global bad_connection
    any_testruns_found = True
    try:
        testruns_resp = c.get('listTestRunsByComponent', json ={'component': objCode })
    except Exception as e:
        any_testruns_found = False
        if e.__class__.__name__ == 'Forbidden' :
            print("got bad connection in <get_testruns_dict>")
            bad_connection = True

    return any_testruns_found, testruns_resp

def get_variable(c,test_response,check_testrun_code,check_var):
    # to fill in this list with the specified variables from *all* tests of this type available
    retVal = []
    # to state if actually found the variable
    foundVar = False
    # find the correct test type
    for testrun in test_response:
        testrun_code = testrun['testType']['code']
        if testrun_code == check_testrun_code:
            # get data for the correct test type
            testID = testrun['id']
            testData = get_testdata(c,testID)
            if bad_connection :
                print(" bad connection, returning ")
                continue
            if testData == None:
                print("didn't find this data type!")

            # find the given property
            for prop in testData['properties']:
                if prop['code'] == check_var:
                    retVal.append( prop['value'] )
                    foundVar = True

            # and, because of the artificial separation of "properties" and "results", 
            #   we have a separate check with a "different" data types
            # find the given result
            for result in testData['results']:
                if result['code'] == check_var:
                    retVal.append( result['value'] )
                    foundVar = True

    if not foundVar :
        print(" didn't find this variable!")
                    
    return retVal


def check_components(c, SN, check_test_code, check_var, Niter):
    global bad_connection

    # connection defaults
    bad_connection = False
    # n_max_restart = 3 # max number of re-authentications, to avoid the infinite loop
    # i_restart = 0 # restart counter

    # loop setup
    n_iter = Niter
    i_iter = 0
    t0 = time.perf_counter()
    tPrev = t0
    while i_iter < n_iter:
        # Slow down to check on the timeout
        # time.sleep(2)

        if bad_connection: break
            # c.user.authenticate()
            # print(" ---------------> Re-authenticated! ")
            # i_iter -= 1 # go back to the previous attempt

        i_iter += 1
        # step 1: to get object code reference
        objCode = get_code(c, SN)
        if bad_connection: break

        # step 2: to get testruns for this object
        found_testruns, testruns_resp = get_testruns_dict(c, objCode)
        if not found_testruns:
            print(" test runs not found for this object, code = ", objCode)
            break
        if bad_connection: break

        # step 3: to part the test runs and get the variable we want
        list_vars = get_variable(c, testruns_resp, check_test_code, check_var)

        # report the iteration
        tNow = time.perf_counter()
        dT = tNow - tPrev
        # print( "tPrev = " + str(tPrev) + ", tNow = " + str(tNow), " deltaT = ", str(tNow-tPrev) )
        tPrev = tNow
        print( "i=", f'{i_iter:04}', 
               "dT =", f'{dT:6.3f}',
               check_var + "( " + SN + ", " + check_test_code + " ) = ", 
               list_vars )

    dT = tPrev - t0 # the total time elapsed: "tPrev" will contain the latest timestamp
    print("Done, the total time is ", f'{dT: 10.3f}' )
    print("i_iter = " + str(i_iter) + " out of " + str(n_iter) + " planned" )
    if bad_connection:
        print(" got bad connection! ")


def main(args):
    SN    = args.SN
    test  = args.test_code
    var   = args.var_code
    Niter = args.Niter
    print(" Got input: ")
    print("   SN        = " + SN   )
    print("   test_code = " + test )
    print("   var_code  = " + var  )
    print("   Niter     = " + str(Niter) )

    client = itkdb.Client( expires_after=dict(days=1) )

    check_components(client, SN, test, var, Niter)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description = 'simple repeat query of DB')
    parser.add_argument('-s', '--SN', dest = 'SN', type = str, default = '20USESX0000599', help = 'Serial Number to check')
    parser.add_argument('-t', '--test_code', dest = 'test_code', type = str, default = 'MANUFACTURING18', help = 'Test handle/code')
    parser.add_argument('-v', '--var_code', dest = 'var_code', type = str, default = 'SUBSTRATE_LOT_NUMBER', help = 'Variable handle/code')
    parser.add_argument('-n', '--Niter', dest = 'Niter', type = int, default = 1, help = 'Number of repeat requests (for profiling)')

    args = parser.parse_args()

    main(args)
