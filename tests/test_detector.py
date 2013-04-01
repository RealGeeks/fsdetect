import os

import mock
import pytest

from fsdetect import Detector

#
# 'create' event
#

def test_should_detect_file_creation(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create)

    basedir.join('myfile.txt').write('')
    detector.check()

    assert on_create.call_count == 1


def test_should_detect_directory_creation(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create)

    basedir.mkdir('subdir')
    detector.check()

    assert on_create.call_count == 1


def test_should_detect_nested_file_creation(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create)

    basedir.mkdir('subdir')
    basedir.join('subdir').join('file.txt').write('')
    detector.check()

    assert on_create.call_count == 2


def test_should_detect_file_creation_recursivelly(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.mkdir('sub1').mkdir('sub2')
    on_create = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create)

    basedir.join('sub1/sub2/file.txt').write('')
    detector.check()

    assert on_create.call_count == 1


def test_should_provide_object_with_pathname_attribute_to_handler_on_file_creation(tmpdir):
    basedir = tmpdir.mkdir('mydir')

    def on_create(event):
        assert event.pathname == str(basedir.join('file.txt'))

    detector = Detector(str(basedir))
    detector.on('create', on_create)

    basedir.join('file.txt').write('')
    detector.check()


#
# handlers chainning
#

def test_should_allow_multiple_handlers(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create1 = mock.Mock(return_value=None)
    on_create2 = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create1)
    detector.on('create', on_create2)

    basedir.join('myfile.txt').write('')
    detector.check()

    assert on_create1.call_count == 1
    assert on_create2.call_count == 1


def test_should_allow_handler_to_prevent_next_handlers_on_chain_to_be_called(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create1 = mock.Mock(return_value=True)
    on_create2 = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create1)
    detector.on('create', on_create2)

    basedir.join('myfile.txt').write('')
    detector.check()

    assert on_create1.call_count == 1
    assert on_create2.call_count == 0


def test_should_let_handler_exceptions_be_raised_and_abort_chain(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    on_create1 = mock.Mock(side_effect=ValueError)
    on_create2 = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('create', on_create1)
    detector.on('create', on_create2)

    basedir.join('myfile.txt').write('')

    with pytest.raises(ValueError):
        detector.check()

    assert on_create1.call_count == 1
    assert on_create2.call_count == 0

#
# 'delete' event
#

def test_should_detect_file_removal(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('myfile.txt').ensure(file=True)
    on_delete = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('delete', on_delete)

    os.remove(str(basedir.join('myfile.txt')))
    detector.check()

    assert on_delete.call_count == 1


def test_should_detect_directory_removal(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('dir1').ensure(dir=True)
    on_delete = mock.Mock(return_value=None)

    detector = Detector(str(basedir))
    detector.on('delete', on_delete)

    os.rmdir(str(basedir.join('dir1')))
    detector.check()

    assert on_delete.call_count == 1


def test_should_provide_object_with_pathname_attribute_to_handler_on_file_removal(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('dir1').ensure(dir=True)

    def on_delete(event):
        assert event.pathname == str(basedir.join('dir1'))

    detector = Detector(str(basedir))
    detector.on('delete', on_delete)

    os.rmdir(str(basedir.join('dir1')))
    detector.check()

#
# 'move' event
#

def test_should_detect_file_move(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('old.txt').ensure(file=True)
    on_move = mock.Mock(return_value=True)

    detector = Detector(str(basedir))
    detector.on('move', on_move)

    os.rename(str(basedir.join('old.txt')),
              str(basedir.join('new.txt')))
    detector.check()

    assert on_move.call_count == 1


def test_should_detect_directory_move(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('olddir').ensure(dir=True)
    on_move = mock.Mock(return_value=True)

    detector = Detector(str(basedir))
    detector.on('move', on_move)

    os.rename(str(basedir.join('olddir')),
              str(basedir.join('newdir')))
    detector.check()

    assert on_move.call_count == 1


def test_should_provide_object_with_pathname_and_src_pathname_attributed_to_handler(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('old.txt').ensure(file=True)

    def on_move(event):
        assert event.pathname == str(basedir.join('new.txt'))
        assert event.src_pathname == str(basedir.join('old.txt'))

    detector = Detector(str(basedir))
    detector.on('move', on_move)

    os.rename(str(basedir.join('old.txt')),
              str(basedir.join('new.txt')))
    detector.check()


def test_should_detect_file_move_from_outside_watched_directory(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched')
    basedir.join('old.txt').ensure(file=True)
    # there is a file on base/old.txt and we are going to watch
    # base/watched/ diretory. we will detect when old.txt is
    # moved to base/watched/new.txt

    on_move = mock.Mock(return_value=None)

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_move)

    os.rename(str(basedir.join('old.txt')),
              str(basedir.join('watched', 'new.txt')))
    detector.check()

    assert on_move.call_count == 1


def test_should_receive_empty_src_pathname_when_file_was_moved_from_outside_watched_directory(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched')
    basedir.join('old.txt').ensure(file=True)

    def on_move(event):
        assert event.src_pathname is None

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_move)

    os.rename(str(basedir.join('old.txt')),
              str(basedir.join('watched', 'new.txt')))
    detector.check()


def test_should_detect_file_move_from_inside_watched_directory_to_outside(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched').join('old.txt').ensure(file=True)
    # there is a file file inside 'base/watched', the directory we
    # are watching. we are going to move this file to outside
    # the directory we are watching, to 'base/'

    on_move = mock.Mock(return_value=None)

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_move)

    os.rename(str(basedir.join('watched', 'old.txt')),
              str(basedir.join('new.txt')))
    # there is a small problem here, if this event (IS_MOVED_FROM)
    # happened just before an IN_MOVED_TO it means the file is being
    # moved inside our watched directory, but this case we handle
    # catching the IN_MOVED_TO event.
    # what we are simulating here is when the next event has no relation
    # with the file move.
    # so unfortunately the detector has to wait until the next event
    # until he makes a decision.
    # so let's create a file just to fire another unrelated event
    detector.check()
    assert on_move.call_count == 0

    basedir.join('watched', 'useless.txt').ensure(file=True)
    detector.check()

    assert on_move.call_count == 1


def test_should_correctly_detect_two_consecutive_moves_from_inside_watched_directory_to_outside(tmpdir):
    pass
