from distutils.sysconfig import get_python_lib

from setuptools import setup


setup(
    name='easyconf',
    version='1.2',
    author='Michael Doronin',
    author_email='warrior2031@mail.com',
    install_requires=['jsonschema', 'split>=1.0'],
    py_modules=['easyconf', 'config_loader'],
    license='MIT',
    data_files=[
        (get_python_lib(), ['autoimport.pth'])
    ],
    classifiers=(
        'Programming Language :: Python :: 3.5',
    ),
    dependency_links=(
        'https://github.com/purpleP/python-split/archive/1.1.zip',
    ),
)
