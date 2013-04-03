import time
import os
from collections import defaultdict
from collections import namedtuple

import pyinotify


__all__ = 'Detector', 'Event'


Event = namedtuple('Event', ('pathname', 'src_pathname'))

class Detector(object):
    '''
    Watches for events on a single file or directory

    Multiple calls to `on()` can be made to detect multiple events.
    `check()` needs to be called periodically to call fire the event
    handlers.

    '''

    check_timeout = 10  # milliseconds

    def __init__(self, directory):
        self._directory = directory
        self._manager = pyinotify.WatchManager(
            exclude_filter=is_hidden
        )
        self._notifier = pyinotify.Notifier(
            self._manager,
            self._on_event,
            timeout=self.check_timeout,
        )
        self._wds = None
        self._full_mask = None
        self._handlers = defaultdict(list)
        self._previous_moved_from = None

    def on(self, event_name, handler):
        '''
        Adds new handler to event.

        `event` is the event name to be watched.

        Works for all pyinotify events, with a small syntax change, removing
        the 'IN_' prefix and lowercase, ex: 'IN_CREATE' becomes 'create'

        There is a special event 'move' that handles 'IN_MOVED_FROM' and
        'IN_MOVED_TO', see README.md for more details.

        `handler` should be a callable.

        Multiple calls with same 'event' will chain the handlers, if any handler
        returns `True` the next handlers won't be called.

        Every handler reveives an instance of `Event` object. This object is not
        the same as pyinotify event. Depending on the event being handled it
        can have `pathname` and/or `src_pathname` attributes.

        '''
        if event_name == 'move':
            mask = pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
            maskname = 'MOVE'
        else:
            mask = pyinotify.EventsCodes.OP_FLAGS['IN_' + event_name.upper()]
            maskname = pyinotify.EventsCodes.maskname(mask)

        if self._wds is not None:
            self._full_mask |= mask
            self._manager.update_watch(self._wds.values(), mask=self._full_mask,
                                       rec=True, auto_add=True)
        else:
            self._full_mask = mask
            self._wds = self._manager.add_watch(self._directory, mask=self._full_mask,
                                                rec=True, auto_add=True)

        self._handlers[maskname].append(handler)
        return self

    def check(self):
        '''
        Must be called periodically to fire the handlers, usually inside
        a loop in the main application.

        Will block for `self.check_timeout` milliseconds

        '''
        self._notifier.process_events()
        while self._notifier.check_events():
            self._notifier.read_events()
            self._notifier.process_events()

    def ignored(self, raw_event):
        '''
        Called when any event is received to verify if it should be ignored.
        By default ignores hidden files.

        '''
        return is_hidden(raw_event.pathname)

    def _on_event(self, raw_event):
        if self.ignored(raw_event):
            return
        elif raw_event.mask & pyinotify.IN_MOVED_FROM:
            self._handle_previous_moved_from()
            self._previous_moved_from = raw_event
        elif raw_event.mask & pyinotify.IN_MOVED_TO:
            self._previous_moved_from = None
            event = Event(raw_event.pathname, getattr(raw_event, 'src_pathname', None))
            self.notify_handlers_2('MOVE', event)
        else:
            self._handle_previous_moved_from()
            event = Event(raw_event.pathname, None)
            maskname = self._parse_maskname(raw_event)
            self.notify_handlers_2(maskname, event)

    def _parse_maskname(self, raw_event):
        if raw_event.mask & pyinotify.IN_ISDIR:
            return raw_event.maskname.replace('|IN_ISDIR', '')
        else:
            return raw_event.maskname

    def _handle_previous_moved_from(self):
        if self._previous_moved_from is not None:
            event = Event(None, self._previous_moved_from.pathname)
            self.notify_handlers_2('MOVE', event)
            self._previous_moved_from = None

    def notify_handlers_2(self, maskname, event):
        for handler in self._handlers[maskname]:
            if handler(event):
                break


def is_hidden(pathname):
    '''
    Returns True if `pathname` is a hidden file or directory

    '''
    return os.path.split(pathname)[1].startswith('.')
