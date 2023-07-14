Software for obtaining "simple" information from DB
==================================================

batch_thickness_report.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python batch_thickness_report.py [-b BatchID [-d]]
```

This script retrieves all sensors and halfmoons corresponding to the batch in question, then pulls their thickness test data. The option "-d" is for extra debugging printout.


simple_query_check.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python simple_query_check.py [-s SN -t test_code -v variable_code [-n N_iterations]]
```

This script retrieves a variable value for a given test code and SN. Can run repeatedly for timing the DB interactions if n_iterations > 1.



simple_test_download.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python simple_test_download.py [-s SN -t test_code ]
```

This script retrieves a JSON file for a particular SN and the test code, then writes it to a file "{SN}_{test_code}_{test_number}.json". If there are multiple tests uploaded to the SN object with the same test number, all files will be downloaded and written (hence, "test_number" quantity).





