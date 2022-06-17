#!/usr/bin/env python

from distutils.core import setup

setup(
      name = 'fruitfly'
   ,  version = '0.1.4'
   ,  description = 'Modular event-driven framework.'
   ,  long_description = 'Framework for minimalist, modular, event-driven embedded applications. Intended for use on small Linux systems like the Raspberry Pi.'
   ,  author = 'Derp Ston'
   ,  author_email = 'derpston+pypi@sleepygeek.org'
   ,  url = 'https://github.com/derpston/fruitfly'
   ,  install_requires = ['PyYAML']
   ,  packages = ['fruitfly']
   )

