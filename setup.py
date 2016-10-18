from setuptools import setup


setup(
    name='easyconf',
    version='0.1',
    author='Michael Doronin',
    author_email='warrior2031@mail.com',
    install_requires=['jsonschema', 'more_functools', 'split'],
    py_modules=['parser'],
    license='MIT',
    classifiers=(
        'Programming Language :: Python :: 3.5',
    ),
)
