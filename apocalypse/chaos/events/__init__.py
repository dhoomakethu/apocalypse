"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

import os
import sys
import random
EventsFolder = os.path.dirname(__file__)

sys.path.insert(0, EventsFolder)


def random_event_gen(event_list):
    last = next = None
    while True:
        while next == last:
            next = random.choice(event_list)
        yield next
        last = next


class ChaosEvents(object):
    """
    finds all chaos events from the Events folder and registers with the
    executor class on load (dynamic)
    """
    events = []
    services = []

    @classmethod
    def update_events(cls):
        possible_events = [mod for mod in os.listdir(EventsFolder)
                           if mod not in ["__init__.py", "base.py"] and
                           mod.endswith(".py")]
        for i in possible_events:
            location = os.path.join(EventsFolder, i)
            if os.path.isfile(location):
                name = os.path.splitext(os.path.basename(location))[0]
                __import__(name)
