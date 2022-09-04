import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')) as fp:
    install_requires = fp.read().splitlines()

setup(
    version='1.0a',
    name='newalbums',
    description='A Spotify Playlist Curation Bot',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    test_suite='tests',
    zip_safe=False,
    install_requires=install_requires,
)
