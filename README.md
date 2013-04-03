# fsdetect - a simpler API to pyinotify [![Build Status](https://travis-ci.org/RealGeeks/fsdetect.png?branch=master)](https://travis-ci.org/RealGeeks/fsdetect)

This project doesn't aim to replace [pyinotify](https://github.com/seb-m/pyinotify),
just offers a simpler API for some situations.

Works on python >= 2.6, but not on python 3 yet.

## Usage

To detect if a file was created inside a directory:

```python
from fsdetect import Detector

def on_create(event):
    print event.pathname

detector = Detector('/tmp/files')
detector.on('create', on_create)

# from now on every `IN_CREATE` event will be detected, to
# fire the handlers use:
detector.check()

```
`.check()` method should be called periodically, easier to hook in your own
loop and runs in the same thread.

This works for every `inotify` event, just translate the syntax from `IN_CREATE` to `create`.

### Handling `IN_MOVED_FROM` and `IN_MOVED_TO`

`inotify` uses a pair of events to detect if a file was moved: `IN_MOVED_FROM`
and `IN_MOVED_TO`. `'move'` simplifies this:

```python
from fsdetect import Detector

def on_move(event):
    print event.pathname or '<unknown destination>'
    print event.src_pathname or '<unknown source>'

detector = Detector('/tmp/files')
detector.on('move', on_move)

# move some files...
detector.check()
```

`on_move` will be called in one of these conditions:

- a file was moved inside the `'/tmp/files'`, something like
  `mv /tmp/files/old.txt /tmp/files/new.txt`. In this case `src_pathname = '/tmp/files/old.txt'`
  and `pathname = '/tmp/files/new.txt'
- a file was moved from outside into the watched directory, like
  `mv /tmp/old.txt /tmp/files/new.txt`. In this case `src_pathname = None` and
  `pathname = '/tmp/files/new.txt'`
- a file was moved from inside the watched directory to outside, like
  `mv /tmp/files/old.txt /tmp/new.txt`. In this case `src_pathname = '/tmp/files/old.txt'` and
  `pathname = None`

In order to implement this behaviour in the third case, a `IN_MOVED_FROM` event is detected
but the handler is not called until the next event arrived, to be able to verify if the
destination will be known or not.

### Ignoring hidden files and directories

Hidden files and directories are automatically ignored. The internal pyinotify `WatchManager`
instance is configured to ignore hidden paths, so they are not watched.

But if a hidden file is created (or any other event) inside a watched directory
there is no way to tell pyinotify to don't watch this file
(see [this issue](https://github.com/seb-m/pyinotify/issues/31) for details).
`fsdetect` handles this case ignoring the received events related to hidden files.

### Contributing

Create a fork of the [repository on github](https://github.com/realgeeks/fsdetect), make your
changes and send a pull request. Make sure your feature/bugfix has enough test coverage.

Inside your fork directory, preferably using a [virtualenv](http://www.virtualenv.org/),
install the package for development plus the test dependencies:

    $ pip install -e .
    $ pip install -r requirements-dev.txt

Run the tests:

    $ ./runtests
