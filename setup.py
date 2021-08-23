#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='libnadagclient',
    version='0.0.2',
    description='Client library for the geotechnical database',
    long_description="""Client library for the geotechnical database at https://geo.ngu.no/kart/nadag/""",
    long_description_content_type="text/markdown",
    author='Egil Moeller',
    author_email='em@emeraldgeo.no',
    url='https://github.com/emerald-geomodelling/libnadagclient',
    packages=setuptools.find_packages(),
    install_requires=[
        "requests-html",
        "libsgfdata >= 0.0.8",
        "owslib"
    ],
)
