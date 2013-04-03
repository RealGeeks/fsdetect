'''
Example of watching the directory recursivelly.

Every new file/directory created/removed/moved will
be detected.

'''
import time
from fsdetect import Detector


def on_move(event):
    # depending on where the files was moved from/to we might
    # not know the source or destination
    # see README.md for more details
    print 'moved {0} to {1}'.format((event.pathname or '<unknown destination>'),
                                    (event.src_pathname or '<unknown source>'))

def on_create(event):
    print 'created: ', event.pathname

def on_delete(event):
    print 'deleted: ', event.pathname


detector = Detector('/tmp/files')
detector.on('create', on_create) \
        .on('move', on_move) \
        .on('delete', on_delete)


while 1:
    detector.check()
    # do some real work...
    time.sleep(0.5)
