from setuptools import setup
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    sys.exit('Sorry, Python 2 < 2.7 is not supported')

if sys.version_info[0] == 3 and sys.version_info[1] < 3:
    sys.exit('Sorry, Python 3 < 3.3 is not supported')

setup(
    name="arborq",

    version="0.9.2",

    description="A Python package to query Arbor PeakFlow SP devices.",
    long_description=long_description,
    url="https://github.com/esnet/arborq",

    author="Jon M. Dugan",
    author_email="jdugan@es.net",

    license="BSD",

    classifiers=[
        "Development Status :: 5 - Production / Stable",

        "Intended Audience :: Developers",

        "Topic :: System :: Networking :: Monitoring",

        "Programming Language :: Python :: 2.7",
    ],

    keywords="network measurement",

    py_modules=["arborq"],

    install_requires=[
        "requests",
        "pytz",
        #"pypond", # XXX: TODO Fix this install, possibly by just publishing pypond
    ],

    extras_require={
        "test": "pytest",
    },

    dependency_links=[
        "git+https://github.com/esnet/pypond.git@master#egg=pypond",
    ]
)
