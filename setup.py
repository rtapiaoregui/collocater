#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:03:13 2020

@author: rita
"""


import os
from setuptools import setup

setup(
    name = "collocater",
    version = "0.3",
    author = "Rita Tapia Oregui",
    author_email = "rtapiaoregui@gmail.com",
    description = ("Package for retrieving collocations from text with Spacy"),
    long_description_content_type="text/markdown",
    keywords = "Collocations Finder",
    url = "https://github.com/rtapiaoregui/collocater",
    packages=['collocater'],
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    install_requires=[
            'beautifulsoup4>=4.6.3',
            'joblib>=0.14.1',
            'lxml>=4.2.5',
            'pandas>=1.0.1',
            'regex>=2018.1.10',
            'requests>=2.21.0',
            'spacy>=2.2.3'
            ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'spacy'],
    include_package_data=True,
    )
