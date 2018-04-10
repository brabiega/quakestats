from setuptools import setup

setup(
    name='quakestats',
    version='0.9.21',
    long_description=__doc__,
    packages=[
        'quakestats',
        'quakestats.datasource',
        'quakestats.dataprovider',
        'quakestats.dataprovider.quake3',
        'quakestats.scripts',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask', 'pymongo', 'pandas', 'pyzmq', 'Flask-PyMongo',
        'passlib',
    ],
)
