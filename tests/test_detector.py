import os

import mock
import pytest

from fsdetect import Detector, is_hidden

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

def test_should_detect_file_normal_move(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('old.txt').ensure(file=True)
    on_move = mock.Mock(return_value=True)

    detector = Detector(str(basedir))
    detector.on('move', on_move)

    os.rename(str(basedir.join('old.txt')),
              str(basedir.join('new.txt')))
    detector.check()

    assert on_move.call_count == 1


def test_should_detect_directory_normal_move(tmpdir):
    basedir = tmpdir.mkdir('mydir')
    basedir.join('olddir').ensure(dir=True)
    on_move = mock.Mock(return_value=True)

    detector = Detector(str(basedir))
    detector.on('move', on_move)

    os.rename(str(basedir.join('olddir')),
              str(basedir.join('newdir')))
    detector.check()

    assert on_move.call_count == 1


def test_should_provide_object_with_pathname_and_src_pathname_attributed_to_handler_on_normal_move(tmpdir):
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


def test_should_provide_object_with_pathname_and_empty_src_pathname_when_moved_from_outside_into_watched_dir(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched')
    basedir.join('old.txt').ensure(file=True)

    def on_move(event):
        assert event.pathname == str(basedir.join('watched', 'new.txt'))
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


def test_should_provide_object_with_empty_pathname_and_src_pathname_when_moved_from_inside_watched_dir_to_outsite(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched').join('old.txt').ensure(file=True)

    def on_move(event):
        assert event.pathname is None
        assert event.src_pathname == str(basedir.join('watched', 'old.txt'))

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_move)

    os.rename(str(basedir.join('watched', 'old.txt')),
              str(basedir.join('new.txt')))
    basedir.join('watched', 'useless.txt').ensure(file=True)
    detector.check()


def test_should_correctly_detect_two_consecutive_moves_from_inside_watched_directory_to_outside(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched')
    basedir.join('watched', 'old1.txt').ensure(file=True)
    basedir.join('watched', 'old2.txt').ensure(file=True)

    on_move = mock.Mock(return_value=None)

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_move)

    os.rename(str(basedir.join('watched', 'old1.txt')),
              str(basedir.join('new1.txt')))
    os.rename(str(basedir.join('watched', 'old2.txt')),
              str(basedir.join('new2.txt')))
    basedir.join('watched', 'useless.txt').ensure(file=True)

    detector.check()

    assert on_move.call_count == 2


def test_should_provide_consistent_object_with_consecutive_moves_from_inside_watched_dir_to_outsie(tmpdir):
    basedir = tmpdir.mkdir('base')
    basedir.mkdir('watched')
    basedir.join('watched', 'old1.txt').ensure(file=True)
    basedir.join('watched', 'old2.txt').ensure(file=True)

    def on_first_move(event):
        assert event.pathname is None
        assert event.src_pathname == str(basedir.join('watched', 'old1.txt'))
    def on_second_move(event):
        assert event.pathname is None
        assert event.src_pathname == str(basedir.join('watched', 'old2.txt'))

    handlers = [on_first_move, on_second_move]
    def on_consecutive_moves(event):
        handlers.pop(0)(event)

    detector = Detector(str(basedir.join('watched')))
    detector.on('move', on_consecutive_moves)

    os.rename(str(basedir.join('watched', 'old1.txt')),
              str(basedir.join('new1.txt')))
    os.rename(str(basedir.join('watched', 'old2.txt')),
              str(basedir.join('new2.txt')))
    basedir.join('watched', 'useless.txt').ensure(file=True)

    detector.check()


#
# multiples events
#

def test_should_listen_to_multiple_events(tmpdir):
    on_create = mock.Mock(return_value=None)
    on_delete = mock.Mock(return_value=None)
    on_move = mock.Mock(return_value=None)

    detector = Detector(str(tmpdir))
    detector.on('create', on_create)
    detector.on('delete', on_delete)
    detector.on('move', on_move)

    # create
    tmpdir.join('file.txt').ensure(file=True)
    # move
    os.rename(str(tmpdir.join('file.txt')), str(tmpdir.join('doc.txt')))
    # delete
    os.remove(str(tmpdir.join('doc.txt')))

    detector.check()

    assert on_create.call_count == 1
    assert on_delete.call_count == 1
    assert on_move.call_count == 1


def test_should_allow_nested_on_method_calls(tmpdir):
    on_create = mock.Mock(return_value=None)
    on_delete = mock.Mock(return_value=None)

    detector = Detector(str(tmpdir))
    detector.on('create', on_create) \
            .on('delete', on_delete)

    # create
    tmpdir.join('file.txt').ensure(file=True)
    # delete
    os.remove(str(tmpdir.join('file.txt')))

    detector.check()

    assert on_create.call_count == 1
    assert on_delete.call_count == 1


#
# ignore hidden files
#

def test_should_not_watch_hidden_directories(tmpdir):
    # hidden directories are not watched
    tmpdir.join('dir1').ensure(dir=True)
    tmpdir.join('dir1', '.dir2').ensure(dir=True)

    on_create = mock.Mock(return_value=None)
    on_delete = mock.Mock(return_value=None)

    detector = Detector(str(tmpdir))
    detector.on('create', on_create) \
            .on('delete', on_delete)

    # create normal file inside hidden directory
    tmpdir.join('dir1', '.dir2', 'doc.txt').ensure(file=True)
    assert_not_called(detector, on_create)

    # delete normal file inside hidden directory
    os.remove(str(tmpdir.join('dir1', '.dir2', 'doc.txt')))
    assert_not_called(detector, on_delete)


def test_should_ignore_events_for_hidden_files(tmpdir):
    # events for hidden files inside watched directory are ignored
    tmpdir.join('dir1').ensure(dir=True)

    on_create = mock.Mock(return_value=None)
    on_delete = mock.Mock(return_value=None)

    detector = Detector(str(tmpdir))
    detector.on('create', on_create) \
            .on('delete', on_delete)

    # create hidden file
    tmpdir.join('dir1', '.file.txt').ensure(file=True)
    assert_not_called(detector, on_create)

    # delete hidden file
    os.remove(str(tmpdir.join('dir1', '.file.txt')))
    assert_not_called(detector, on_delete)


def test_should_not_ignore_hidden_files_when_renamed_to_visible_files(tmpdir):
    tmpdir.join('dir1').ensure(dir=True)

    on_move = mock.Mock(return_value=None)

    detector = Detector(str(tmpdir))
    detector.on('move', on_move)

    tmpdir.join('.invisible.pdf').ensure(file=True)
    os.rename(str(tmpdir.join('.invisible.pdf')),
              str(tmpdir.join('visible.pdf')))

    detector.check()

    assert on_move.call_count == 1

#
# is_hidden() helper function
#

def test_is_hidden():
    assert is_hidden('/tmp/.file.txt')
    assert is_hidden('/tmp/.file.out.txt')
    assert is_hidden('/tmp/sub/dir/.file.txt')
    assert is_hidden('/tmp/.dir')
    assert is_hidden('/tmp/sub/dir/.hidden')
    assert not is_hidden('/tmp/file.txt')
    assert not is_hidden('/tmp/sub/dir/doc.pdf')
    assert not is_hidden('/tmp/dir1/dir2')


#
# asserts
#

def assert_not_called(detector, handler):
    detector.check()
    assert handler.call_count == 0
