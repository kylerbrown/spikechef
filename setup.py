from __future__ import print_function
from setuptools import setup
import io
import os
import spikechef

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')

setup(
    name='spikechef',
    scripts=['run_spikechef'],
    version=spikechef.__version__,
    url='http://github.com/kylerbrown/spikechef/',
    license='MIT License',
    author='Kyler Brown',
    author_email='kylerjbrown@gmail.com',
    description='arf wrapper for klusta suite',
    long_description=long_description,
    packages=['spikechef'],
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        ],
)

