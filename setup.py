from setuptools import setup
from distutils.sysconfig import get_python_lib


setup(
    name='easyconf',
    version='0.1',
    author='Michael Doronin',
    author_email='warrior2031@mail.com',
    install_requires=['jsonschema', 'more_functools', 'split>=1.0'],
    py_modules=['easyconf'],
    license='MIT',
    data_files=[
        (get_python_lib(), ['autoimport.pth'])
    ],
    classifiers=(
        'Programming Language :: Python :: 3.5',
    ),
    dependency_links=(
        'https://github.com/purpleP/more_functools/tarball/master#egg=more_functools-1.0',
        'https://bitbucket.org/warrior2031/python-split/get/tip.zip#egg=split-1.0',
    ),
)
