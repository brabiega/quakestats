from setuptools import setup, find_packages
from os import path
# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

import quakestats

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='quakestats',
    version=quakestats.VERSION,
    description='Quake 3 / Quake Live match processing app',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/brabiega/quakestats',
    author='Bartoszer',
    author_email='bartoszer@bajt.ovh',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='quake stats statistics match analysis visualize',

    packages=find_packages(
        include=['quakestats*'],
    ),
    entry_points={
        'console_scripts': [
            'quakestats = quakestats.__main__:main',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask>=1.0',
        'Flask-PyMongo',
        'pandas',
        'passlib',
        'pymongo',
        'pyzmq',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/brabiega/quakestats/issues',
        'Source': 'https://github.com/brabiega/quakestats',
    },
)
