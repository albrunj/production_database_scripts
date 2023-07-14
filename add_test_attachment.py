#!/usr/bin/env python
import argparse
import os
import sys

import itk_pdb.dbAccess as dbAccess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add attachment to test run of component in production database")
    parser.add_argument("--code", help="DB code of test run")
    parser.add_argument("--title", help="Short description")
    parser.add_argument("--message", "-m", dest="message", help="Comment about attachment")
    parser.add_argument("--file", help="File to attach")
    parser.add_argument("--file-name-override", help="Override file-name of attachment")
    parser.add_argument("--test", action="store_true", help="Don't write to DB")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    if not args.code:
        print("Need code of test run, from listTestRunsByComponent")
        sys.exit(1)

    if not args.file:
        print("Need name of file to attach")
        sys.exit(1)

    if not args.title:
        print("Need short message (title)")
        sys.exit(1)

    if not args.message:
        print("Don't have a long message")
        sys.exit(1)

    print("Add attachment to test run:")
    print("    Code for test run: %s" % args.code)
    print("    Short: %s" % args.title)
    if args.file_name_override:
        print("    File-name: %s (known as %s)" % (args.file, args.file_name_override))
    else:
        print("    File-name: %s" % args.file)

    print("    Message: %s" % args.message)

    if args.test:
        print("Exit early for testing")
        sys.exit(1)

    try:
        data = {}
        data["testRun"] = args.code
        # Not a link
        data["type"] = "file"
        data["title"] = args.title
        data["description"] = args.message

        if args.file_name_override:
            attachment = {"data": (args.file_name_override, open(args.file, 'rb'))}
        else:
            attachment = {"data": open(args.file, 'rb')}
        result = dbAccess.doSomething("createTestRunAttachment",
                                      data, attachments = attachment)
        # Responds with info on the component...
        if args.verbose:
            print(result)
        else:
            if "uuAppErrorMap" in result:
                errInfo = result["uuAppErrorMap"]
                if len(errInfo) == 0:
                    print("Attachment added successfully")
                else:
                    print("Indeterminate result:")
                    print(result)
            else:
                # This would be the case in older versions
                print("Indeterminate result:")
                print(result)

    except Exception:
        if args.verbose:
            print("Request failed:")
            import traceback
            traceback.print_exc()
        else:
            print("Request failed, use --verbose flag for more information")
