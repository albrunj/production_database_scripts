Software for setting up a test structure in DB
==================================================

get_test_structure.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python get_test_structure.py [-c componentType -t testType -o outputFile]
```

This script downloads the test structure from DB for a particular <componentType> and <testType> combination, then dumps the JSON structure to the <outputFile>.


make_test_json.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python make_test_json.py [-i inputControlFile -o outputFile [-p printTemplate]]
```

This script rewrites an input control file (written in the described text structure) to a JSON file amenable to the setting up the DB test structure. The option *-p* would only print the template for the input control file and exit.



set_test_json.py
*Written by Vitaliy Fadeyev. For any comments, please contact fadeyev@ucsc.edu*

```bash 
python set_test_json.py [-j inputJSONfile ]
```

This script takes an input JSON file and sets up the DB test with its content.





