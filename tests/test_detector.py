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


def test_should_provide_object_with_pathname_attribute_to_handler(tmpdir):
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
