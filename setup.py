#!/usr/bin/env python

from distutils.core import setup

setup(
    name='zero_deploy',
    version='0.1.0',
    description='Manange enviroment wich the code will be executed',
    author='Rodrigo Baron <baron.rodrigo0@gmail.com>',
    url='https://github.com/rodrigobaron/zero_deploy',
    packages=['zero_deploy'],
    install_requires=[
    	'plumbum',
    	'pyyaml'
    ],
    dependency_links=[
      'git+https://github.com/tomerfiliba/rpyc',
  	]
)