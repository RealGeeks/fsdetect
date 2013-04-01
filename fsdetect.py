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
            self._previous_moved_from = raw_event
            return

        if raw_event.mask & pyinotify.IN_MOVED_TO:
            self._previous_moved_from = None
            self.notify_handlers(raw_event, 'MOVE')
        else:
            if self._previous_moved_from is not None:
                self.notify_handlers(self._previous_moved_from, 'MOVE')
                self._previous_moved_from = None
            self.notify_handlers(raw_event)

    def notify_handlers(self, raw_event, maskname=None):
        if maskname is None:
            maskname = raw_event.maskname
            if raw_event.mask & pyinotify.IN_ISDIR:
                maskname = maskname.replace('|IN_ISDIR', '')

        event = Event(
            raw_event.pathname,
            getattr(raw_event, 'src_pathname', None)
        )

        for handler in self._handlers[maskname]:
            if handler(event):
                break
