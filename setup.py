#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()


requirements = ['click']
setup_requirements = ['pytest-runner']
test_requirements = ['pytest']


setup(
    name='jirosso',
    version='1.0',
    author='chexex',
    autho_email='levisolympus@gmail.com',
    py_modules=['jirosso'],
    include_package_data=True,
    install_requires=[
        'click',
        'jira',
    ],
    entry_points='''
        [console_scripts]
        jirosso=jirosso:cli
    ''',
)
