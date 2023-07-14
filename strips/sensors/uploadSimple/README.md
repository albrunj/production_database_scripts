Software for simple upload of (select) tests to DB
==================================================

upload_json_test.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python upload_json_test.py [-j JSONfile [-r responseFile]]
```

This script uploads an input JSON file as a test result. Optionally the DB response to the upload is recorde in the <responseFile>.


upload_test_image.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python upload_test_image.py [-s SN -i ImageFile [-c Comment]]
```

This script was used to testing the process image upload to DB with a simple specific test structure. For a given <SN> and <ImageFile> (and optional <Comment> field) the 2-step upload was performed.



upload_VI_sensors_V2.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python upload_VI_sensors_V2.py [-i inputFile [-t] [-w] ]
```

This script takes an input configuration file with the results of the visual inspection for multiple sensors (as well as image file names), performs several data integrity checks, then uploads the test resutls to DB. The optional *-t* argument would only print a template for the input configuration file and exit. The optional *-w* argument would write separate/individual files for every sensor listed in the configuration file.







