Scripts for access to the Production Database
=============================================

The scripts in this repository are used to access the ATLAS ITK
Production Database.

They are divided between some simple [command line scripts](#common-scripts)
in this directory and more complex [GUI and reporting scripts](#further-scripts)
in sub-directories. If running on lxplus, no installation should be necessary,
but there are more instructions [below](#installation).

If you have problems using any scripts here, report that
[here](https://gitlab.cern.ch/atlas-itk/sw/db/production_database_scripts/-/issues).

Project Information
===================

## Links

* [ITK Production Database TWiki](https://twiki.cern.ch/twiki/bin/viewauth/Atlas/ITKProductionDatabase)
* [Documentation](https://itk.docs.cern.ch/)
* [Test Web User Interface](https://itkpd-test.unicorncollege.cz/)

## To-Do Lists

Please find links to areas of work that require effort 

* Common [Reporting/Shipping/Interfacing](need link)
* [Strips](https://docs.google.com/spreadsheets/d/1MlKXSoQMxk9qh_zQtbaUx9BBSsKpOcghIaD_O0ZVHQM/edit#gid=0)
* [Pixels](https://docs.google.com/spreadsheets/d/11O1XBtBWYUSa0V3LSKjrAwx8sP_n-2Lksna26p4fQYQ/edit#gid=0)

Authentication
==============

In order to do anything, you need a login token for the production DB.

Once you have a token, you can store it in the environment variable
ITK_DB_AUTH so it is used between python invocations:

```bash
export ITK_DB_AUTH=TOKEN
```

Otherwise, the standard pair of access codes will be requested when a command
is run.

You can request a token by running the following:

```bash
python get_token.py
```

which will print a line that you can then use to store in the environment.

If you have already logged in to the DB using your browser, you can also copy
the token from here:

https://uuidentity.plus4u.net/uu-identitymanagement-maing01/a9b105aff2744771be4daa8361954677/showToken

Common scripts
==============

Reading from the database
-------------------------

There are some simple methods to read data from the database.

Most of the .py files in this directory are designed to be run in this
manner and help information can be found by for example:

```bash
python read_db.py --help
```

To run, use something like:

```bash
python read_db.py list_components # Defaults to Strips project
python read_db.py list_commands
```

More example commands:

```bash
python read_db.py list_test_types --project S --component-type HYBRID
python read_db.py list_component_types # Default to Strips
python read_db.py list_component_types --project P
```

### Component info

You can read all component info using the following:

```bash
python read_db.py get_component_info --component-id COMPONENT_CODE
```

where COMPONENT_CODE is either the code (see the QR code), or the serial number.

TODO: Document other scripts, including compareTests, ComponentLookupGui,
getInventory, generatePlots, inventory2CSV, PlotGUI.

Writing
-------

A few commands are available to write to the database.

In general these require a code parameter to identify a particular
component. This can be found in the output of the following:

```bash
python read_db.py list_components
```

Or, more specifically:

```bash
python read_db.py list_components --component-type HYBRID
```

To register a single component (batch registration is TODO):

```bash
python registerComponent.py
```

To record a comment on a single component:

```bash
python add_comment.py
```

### Test uploads

#### Preparation

In order to upload some test results, you need to generate a json
object, and put it in a file. You can make a prototype of what is
expected for a particular component test with the following:

```bash
python test_prototype.py --project S --component-type HYBRID
```

This will create a prototype_XXX.json file for every test type
of that component.

In order to generate a prototype for only one test, use:

```bash
python test_prototype.py --project S --component-type HYBRID --test-type STROBE_DELAY
```

(which writes only prototype_STROBE_DELAY.json)


#### The upload

Upload the data with (as before $CODE is the component code):

```bash
python upload_test_results.py --test-file file.json --code $CODE
```

### Attachments

You can add an attachment to a component with:

```bash
python add_attachment.py --code $CODE --file file-to-read --title "Some short description" --message "Some longer description"
```

You can add an attachment to a test run with:

```bash
python add_test_attachment.py --code $TEST_RUN_CODE --file file-to-read --title "Some short description" --message "Some longer description"
```

In both cases, the DB can be given a different file name using the argument
--file-name-override.

### Comments

Add a comment to a specific component (different to a comment on a test run).

```bash
python add_comment.py --help
```

### Stages

Move a component to the specified stage

```bash
python set_stage.py --component-id SERIAL_NUMBER --component-stage STAGE
```

### Testing

Create a random hybrid and some chips and assemble one on the other:

```bash
python make_test.py hybrid
```

Further scripts
===============

Information on other scripts is to be found in their own directory.

Shipping
--------

There are some general scripts to do with [shipping](shipping/README.md).

Assembly
--------

A simple GUI for assembling components (primarily strips) is [here](strips/assembly/README.md].

Family Tree
-----------

A utility for plotting relations among components is [here](strips/staves/GetFamilyTree.py].

```bash
python3 strips/staves/GetFamilyTree.py  --component-code MODULE --type-code BARREL_LS_MODULE --component-name 20USBML1234657
```

Strips
------

Scripts mainly for managing strips specific components are [here](strips/README.md].

* [Sensors](strips/sensors/README.md)
* [Modules](strips/modules/README.md)
* [Power boards](strips/pwbs/README.md)
* [Staves](strips/staves/README.md)
* [Hybrids](strips/hybrids/README.md)
* [ASICs](strips/asics/README.md)

Pixels
------

* [Modules](pixels/modules/README.md)
* [Sensors](pixels/sensors/README.md)
* [PCBs](pixels/pcbs/README.md)

Installation
============

This software is compatible with python 3.6 (the default python3 for CentOS7)
and later. In particular the used modules should be installed on lxplus so
that you can many things without further installation.

The main dependency is the `requests` python module, so from a base CentOS7
you will need:

```bash
sudo yum install python36-requests
```

If you have a python installation via other means you can use:

```bash
python -m pip install --user requests
```

For some of the test uploading, the `requests-toolbelt` package is also used:

```bash
python -m pip install --user requests-toolbelt
```

Or:

```bash
sudo yum install python-requests-toolbelt
```

Standard install
----------------

A more standard python installation method can be used, this is currently a
work-in-progress.

```bash
python -m pip install --user -e .
```

This installs in user local directory \~/.local/bin, the -e option means 
changes you make in this directory will be used.
