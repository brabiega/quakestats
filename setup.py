# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import (
    open,
)
from os import (
    path,
)

from setuptools import (
    find_packages,
    setup,
)

from src import (
    quakestats,
)

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
        'Programming Language :: Python :: 3',
    ],
    keywords='quake stats statistics match analysis visualize',
    packages=find_packages(where='src'),
    python_requires='>=3.6, <4',
    package_dir={'': 'src'},
    scripts=[
        'src/quakestats/scripts/q3-log-watch'
    ],
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
        'click>6.5,<7',
        'pandas',
        'passlib',
        'pymongo',
        'pyzmq',
        'requests',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/brabiega/quakestats/issues',
        'Source': 'https://github.com/brabiega/quakestats',
    },
)
