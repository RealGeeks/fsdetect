import time
from collections import defaultdict
from collections import namedtuple

import pyinotify

Event = namedtuple('Event', ('pathname', 'src_pathname'))

class Detector(object):

    def __init__(self, directory):
        self._directory = directory
        self._manager = pyinotify.WatchManager()
        self._notifier = pyinotify.Notifier(
            self._manager,
            self._on_event,
            timeout=10
        )
        self._handlers = defaultdict(list)
        self._previous_moved_from = None

    def on(self, event_name, handler):
        if event_name == 'move':
            mask = pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
            maskname = 'MOVE'
        else:
            mask = pyinotify.EventsCodes.OP_FLAGS['IN_' + event_name.upper()]
            maskname = pyinotify.EventsCodes.maskname(mask)

        self._manager.add_watch(
            path=self._directory,
            mask=mask,
            rec=True,
            auto_add=True
        )
        self._handlers[maskname].append(handler)

    def check(self):
        self._notifier.process_events()
        while self._notifier.check_events():
            self._notifier.read_events()
            self._notifier.process_events()

    def _on_event(self, raw_event):
        if raw_event.mask & pyinotify.IN_MOVED_FROM:
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
