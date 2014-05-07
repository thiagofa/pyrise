#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup, find_packages

setup(name="pyrise",
      version='0.4.3',
      description="Python wrapper for 37Signals Highrise",
      long_description="A work in progress, but one that will be awesome when finished. Pyrise gives you class objects that work a lot like Django models, making the whole experience of integrating with Highrise just a little more awesome and Pythonic.",
      license="MIT License",
      author="Jason Ford",
      author_email="jason@feedmagnet.com",
      url="http://github.com/feedmagnet/pyrise",
      packages = find_packages(),
      install_requires = ['httplib2'],
      keywords= "python 37signals highrise api wrapper feedmagnet",
      )
