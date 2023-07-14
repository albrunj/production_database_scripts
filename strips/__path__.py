#!/usr/bin/env python
# __path__.py

def updatePath():
    import sys
    from os.path import dirname, join, abspath
    depth = 1
    path = abspath(join(dirname(__file__), *(depth * ['..'])))
    if path not in sys.path:
        sys.path.insert(0, path)
