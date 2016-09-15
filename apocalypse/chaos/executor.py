"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
from apocalypse.chaos.events import random_event_gen
from apocalypse.exceptions import UnknownChaosEvent
from apocalypse.utils.logger import get_logger
from apocalypse.utils.helpers import banner

import types

exe_logger = get_logger()


def events():
    return ChaosExecutor.list_events()


def unregister(event):
    ChaosExecutor.unregister(event)


class ChaosExecutor(object):
    """
    Chaos executor class responsible for executing chaos events.
    """

    _category_map = {}
    _chaos_events = {}

    def __init__(self, chaos_app):
        self.app = chaos_app
        self.event_gen = random_event_gen(self._chaos_events.keys())

    def __new__(cls, *args, **kwargs):
        return super(ChaosExecutor, cls).__new__(cls, *args, **kwargs)

    def __call__(self, event, *args, **kwargs):
        _chaos_event = self._chaos_events.get(event)
        if _chaos_event:
            exe_logger.debug("Calling event %s on %s" % (event, self.app))
            if isinstance(_chaos_event, (types.InstanceType,
                                    types.ObjectType, staticmethod)):
                return _chaos_event(self.app, *args, **kwargs)
            elif isinstance(_chaos_event, types.FunctionType):
                return _chaos_event(self, *args, **kwargs)
            else:
                raise UnknownChaosEvent(event)
        else:
            exe_logger.error("Unknown event requested :%s" % event)
            raise UnknownChaosEvent(event)

    @classmethod
    def register(cls, event):
        exe_logger.info("Registering event :%s" % event)
        if isinstance(event, (types.FunctionType, staticmethod)):
            name = event.__name__
            cls._chaos_events[name.upper()] = event
            setattr(cls, name, event)
        elif isinstance(event, types.ClassType) and hasattr(event, "__call__"):
            name = event.__name__
            event = event()
            cls._chaos_events[name.upper()] = event
            setattr(cls, name, event)
        elif (isinstance(event, (types.InstanceType, types.ObjectType))
              and hasattr(event, "__call__")):
            if isinstance(event, type):
                name = event.__name__
                event = event()
            else:
                name = event.__class__.__name__
            cls._chaos_events[name.upper()] = event
            setattr(cls, name, event)

        else:
            name = str(event)
            exe_logger.error("Error registering event :%s" % event)
            raise UnknownChaosEvent("unable to register event %s!!" % name)

    @classmethod
    def unregister(cls, event):
        exe_logger.info("Un-registering event :%s" % event)
        name = event.upper()
        if cls._chaos_events.get(name):
            # if hasattr(self, event):
            #     delattr(self, event)
            del cls._chaos_events[name]

    def run(self, event, *args, **kwargs):
        exe_logger.warning(banner("=", pad=False))
        exe_logger.info("Running event :%s" % event)
        return self.execute(event, *args, **kwargs)

    def random_run(self, *args, **kwargs):
        event = self.event_gen.next()
        exe_logger.warning(banner("=", pad=False))
        exe_logger.info("Running random event :%s" % event)
        return self.run(event, *args, **kwargs)

    @property
    def events(self):
        return sorted(self._chaos_events.keys())

    @classmethod
    def update_events(cls, value):
        event = dict(value)
        for k, v in event.items():
            if not cls._category_map.get(v.category):
                cls._category_map[v.category] = [k.lower()]
            else:
                cls._category_map[v.category].append(k.lower())
        cls._chaos_events.update(event)

    @classmethod
    def list_events(cls):
        return cls._chaos_events

    def execute(self, event, *args, **kwargs):
        exe_logger.debug("Executing event %s" % event)
        event = event.upper()
        try:
            res = self(event, *args, **kwargs)
            exe_logger.info("Done executing chaos event: %s" % event)
            exe_logger.warning(banner("=", pad=False))
            if not res:
                exe_logger.critical("Shit happened!! , event: %s, args: %s, "
                                    "kwargs: %s" % (event, args, kwargs))
            return res
        except AttributeError as e:
            raise UnknownChaosEvent(e)

    def is_registered(self, event):
        exe_logger.info("Checking event %s is registered" % event)
        return event.upper() in self.list_events()

    def build_args(self):
        pass

    def get_events_by_category(self, category):
        return self._category_map.get(category, [])