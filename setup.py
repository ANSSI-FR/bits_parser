#!/usr/bin/env python3
"""bits_parser"""
import sys
assert sys.version_info.major == 3, 'Python 3 required'

import re
from pathlib import Path
from setuptools import setup, find_packages


# read the version number from package
with (Path(__file__).resolve().parent / 'bits' / '__init__.py').open() as f:
    v, = re.search(".*__version__ = '(.*)'.*", f.read(), re.MULTILINE).groups()


setup(

    name='bits_parser',
    version=v,

    author='ANSSI-INM',
    author_email='',

    url='',
    description=__doc__,
    long_description=open('README.rst').read(),

    install_requires=open('requirements.txt').read().splitlines(),

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=[
        'scripts/bits_parser',
    ],
    license='MIT',
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]

)
