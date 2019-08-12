from setuptools import setup

setup(
    name='jirosso',
    version='1.0',
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
