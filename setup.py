#!/usr/bin/env python
from os import path

from setuptools import find_packages
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as readme_md:
    long_description = readme_md.read()

develop_require = [
    "pyflakes",
    "pytest",
    "pytest-cov",
    "pytest-mock",
    "coverage",
    "reorder-python-imports",
]

extras_require = {
    "develop": ["bandit",
                develop_require]
}

setup(
    name="itk_pdb",
    version="0.0.2",
    description="Python wrapper to ITk Production DB",
    long_description=long_description,
    url="https://gitlab.cern.ch/atlas-itk/sw/db/production_database_scripts",
    author="Matthew Basso, Jiayi Chen, Bruce Gallop, Giordon Stark",
    author_email="bruce.gallop@cern.ch, gstark@cern.ch",
    include_package_data=True,
    packages=find_packages(".", exclude=["testing"]),
    install_requires=["requests"],
    extras_require=extras_require,
)
