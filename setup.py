from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arborq",

    version="0.9.0",

    description="A Python package to query Arbor PeakFlow devices",
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

    intall_requires=["requests"],

    extras_require={
        "test": "pytest",
    },
)
