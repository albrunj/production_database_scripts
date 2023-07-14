import argparse
import datetime
import json
import os
import pathlib
import shutil
import time

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import itk_pdb.dbAccess as dbAccess

def read_file(f, institution):
    d = open(f).read()
    data = json.loads(d)

    if "component" in data:
        # OK
        pass
    elif "20US" in f:
        # Extract serial number from filename
        idx = f.find("20US")
        sn = f[idx:idx+14]
        data["component"] = sn
    else:
        print("Need reference to component, hex string")
        return None

    if "institution" in data:
        # OK
        pass
    elif institution is not None:
        data["institution"] = institution
    else:
        print("Need institution to upload, short code")
        return None

    return data
###################################
if __name__ == "__main__":
    sdv = os.getenv("SCTDAQ_VAR")
    if sdv is None:
        results_default = "output_folder"
    else:
        results_default = str(pathlib.Path(sdv) / "results")

    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default=results_default, help='ITSDAQ test output directory (var/results)')
    parser.add_argument("--to-upload-dir", default='upload_folder', help='directory with selected test files to be uploaded')
    parser.add_argument("--upload-done-dir", default='uploaded_folder', help='directory containing successfully uploaded test results')
    parser.add_argument("--backlog-hours", default=24, help='Number of hours in the past to check for new results')
    parser.add_argument("--institution", default = None, help="Institution if not provided in file")
    args = parser.parse_args()
    results_dir = args.results_dir
    to_upload_dir = args.to_upload_dir
    upload_done_dir= args.upload_done_dir
    backlog_hours = args.backlog_hours
    institution = args.institution

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

        #if {message} is 'Token is not valid or is expired':
        #    sys.exit(1)

    filelist = []
    for filename in os.listdir(results_dir):

        f = os.path.join(results_dir, filename)
        filelist.append(filename)
        # add some selection criteria here like time stamp etc

        if not f.endswith ('.json') :
            continue
        
        compare_date = datetime.datetime.today() - datetime.timedelta(hours = backlog_hours)
        create_dt = os.stat(f).st_mtime
        created_date = datetime.datetime.fromtimestamp(create_dt)
        if created_date > compare_date:
            print(f"\nCopying file:  {f} with time stamp", created_date)
            shutil.copy(f, to_upload_dir)

    upload_done_list = os.listdir(upload_done_dir)

    for filename in os.listdir(to_upload_dir):
        f = os.path.join(to_upload_dir, filename)
        if not f.endswith ('.json') :
            continue

        if filename in upload_done_list:
            print(f"File already uploaded: {filename}")
            continue

        testfile = read_file(f, institution)

        named_tuple = time.localtime() # get struct_time
        localtime = time.strftime("%a, %d %b %Y  %H:%M:%S", named_tuple)
        output_line = f'{localtime}, {testfile["testType"]}, runNumber {testfile["runNumber"]}, '

        print(f"\nReading file:  {f} ")
        try:
            print(" running DB Upload")
            results = dbAccess.doSomething("uploadTestRunResults", testfile)

            output_line = output_line + 'upload succesfull\n\n'
            print('upload successful')
            shutil.move(f, upload_done_dir)
        except dbAccess.dbAccessError as dbae:
            error_info = dbae.full_info

            keys = list(error_info.keys())

            if len(keys) == 0:
                output_line = output_line + 'Error: DB error response has no message\n'
            else:
                message = error_info[keys[0]]['message']
                message_type = error_info[keys[0]]['type']

                output_message = f' {message_type} , {message}\n'
                print(output_message)
                output_line = output_line + output_message
        
        with open(upload_done_dir + '/log.txt' , 'a') as errorfile:
            errorfile.write(output_line)
