# pylint: disable=redefined-builtin, invalid-name

from os import path
import sys
from codecs import open

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    sys.exit('Sorry, Python 2 < 2.7 is not supported')

if sys.version_info[0] == 3 and sys.version_info[1] < 3:
    sys.exit('Sorry, Python 3 < 3.3 is not supported')

setup(
    name="arborq",

    version="0.9.3",

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

        "Programming Language :: Python :: 3.3",

        "Programming Language :: Python :: 3.4",

        "Programming Language :: Python :: 3.5",
    ],

    keywords="network measurement",

    py_modules=["arborq"],

    install_requires=[
        "requests",
        "pytz"
    ],

    extras_require={
        "test": "pytest",
    },
)
