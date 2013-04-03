from distutils.core import setup
from os.path import dirname, join

with open(join(dirname(__file__), 'README.md')) as f:
    README = f.read()

setup(
    name='fsdetect',
    version='0.1',
    description='A limited simpler API fo PyInotify',
    long_description=README,
    url='https://github.com/realgeeks/fsdetect',
    author='Real Geeks LLC',
    author_email='igor@realgeeks.com',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Monitoring',
    ],
    license='MIT',
    install_requires=['pyinotify'],
    py_modules=['fsdetect'],
)
