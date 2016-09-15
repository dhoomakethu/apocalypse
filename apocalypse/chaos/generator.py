"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

import random
import re
from copy import deepcopy

from apocalypse.utils.backgroundJob import BackgroundJob
from apocalypse.utils.docker_client import get_host_ip
from apocalypse.utils.logger import get_logger
from apocalypse.utils.proc import TPExecutor
from apocalypse.chaos.executor import ChaosExecutor
from apocalypse.chaos.events import ChaosEvents, random_event_gen

chaos_logger = get_logger()

pid_regexp = re.compile(r"^\d+$")

ChaosEvents.update_events()

SECONDS_PER_TIME_UNIT = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


class ChaosGenerator(object):
    """
    Generates chaos events periodically as supplied from cmd prompt or
    from configuration file
    """

    workers = {}
    max_workers = 10
    error = 0
    error_threshold = 0  # threshold error count
    device_map = []
    event_gen = None

    def __init__(self, chaos_app, events={}, random=True,
                 every=10, max_workers=10, **extras):
        self._chaos_executor = ChaosExecutor(chaos_app=chaos_app)
        self._chaos_list = events
        self.random = random
        self.max_workers = max_workers
        self._parse_time_interval(every)
        self.executor = TPExecutor(max_workers=self.max_workers)
        self.executor.make_deamon()
        self.bg_worker = BackgroundJob("Chaos Generator", self.time_interval,
                                       self._create_chaos)
        self.monitor = BackgroundJob("Monitor", 1, self.monitor_thread_pool)
        self.dirty = False
        self.chaos_triggered = False
        self.extras = extras

    def update_events(self, events):
        self._chaos_list = {k: dict(v.items() + [("done", [])])
                            for k, v in events.items()}
        self.event_gen = random_event_gen(self._chaos_list.keys())

    def chaos(self, event, *args, **kwargs):
        if not event:
            chaos_logger.debug("Running random Chaos event")
            return self._chaos_executor.random_run()
        else:
            chaos_logger.debug("Running Chaos event %s" % event)
            return self._chaos_executor.run(event, *args, **kwargs)

    def is_registered(self, event):
        chaos_logger.info("Checking if '%s' is registered" % event)
        return self._chaos_executor.is_registered(event)

    def register(self, event):
        chaos_logger.info("Registering event '%s' " % event)
        return self._chaos_executor.register(event)

    def unregister(self, event):
        chaos_logger.info("Un-registering event '%s' " % event)
        return self._chaos_executor.unregister(event)

    def start(self):
        """
        Creates chaos from the list of events every n seconds
        Args:
            events: event list from which chaos to be generated
            random: randomly pick a chaos event
            every: trigger chaos evey 'n' seconds

        Returns:
            None

        """
        chaos_logger.info("Staring Chaos!!!!")
        if self.extras['network_chaos']:
            chaos_logger.warning("Running pre-requisites "
                                 "for Network chaos events")

            chaos_logger.warning("All set!!!")

        if self.chaos_triggered:
            self.stop()
        if self.dirty:
            self.bg_worker = BackgroundJob("Chaos Generator",
                                           self.time_interval,
                                           self._create_chaos)
            self.executor = TPExecutor(max_workers=self.max_workers)
            self.monitor = BackgroundJob("Monitor", 1,
                                         self.monitor_thread_pool)
        self.bg_worker.start()
        self.monitor.start()
        self.chaos_triggered = True
        self.dirty = True

    def _create_chaos(self):
        """
        Creates chaos from the list of events every n seconds
        Args:
            events: event list from which chaos to be generated
            random: randomly pick a chaos event
            every: trigger chaos evey 'n' seconds

        Returns:
            None

        """
        chaos_logger.debug("creating chaos")
        if self._chaos_list:
            e_name = self.event_gen.next()
            event = self._chaos_list[e_name]
            if not event['services']:
                event['services'] = self.engine.get_services()
            services = list(set(event['services']) ^ set(event["done"]))
            if not services:
                event["done"] = []
                services = event['services']
            service = random.choice(services) if services else None
            event_copy = deepcopy(event)
            if service:
                event["done"].append(service)
            event_copy.pop("done")
            event_copy["services"] = [service]
            future = self.executor.submit(self.chaos, e_name, **event_copy)

        else:
            future = self.executor.submit(self.chaos, None)
        future.add_done_callback(self._tp_call_back)

    def stop(self):
        chaos_logger.info("Stopping chaos")
        if self.chaos_triggered:
            self.bg_worker.cancel()
            self.chaos_triggered = False
            self.executor.shutdown()
            self.monitor.cancel()

    def set_max_workers(self, count):
        chaos_logger.info("Setting  max worker threads to %s" % count)
        self.max_workers = count

    def list_events(self):
        return self._chaos_executor.list_events()

    @staticmethod
    def _tp_call_back(future):
        try:
            res = future.result()
            if len(res):
                chaos_logger.debug("In future callback: "
                                   "result returned : %s" % res)
                return res
            else:
                chaos_logger.info("No Docker container with given info found")
                chaos_logger.debug("In future callback: current Error "
                                   "count : %s !!" % ChaosGenerator.error)
                ChaosGenerator.error += 1
        except Exception as e:
            chaos_logger.critical("Exception while "
                                  "running threadpool job : %s" % e)
            ChaosGenerator.error += 1
            return e

    def monitor_thread_pool(self):
        chaos_logger.debug("In monitor thread")
        chaos_logger.debug("current Error "
                           "count : %s !!" % ChaosGenerator.error)
        if ChaosGenerator.error >= ChaosGenerator.error_threshold:
            chaos_logger.critical("Errors observed while "
                                  "running chaos generator, check if "
                                  "the environment is up and running")
            chaos_logger.critical("Force Stopping Chaos!!!")
            self.stop()

    @classmethod
    def set_threshold(cls, error_threshold):
        cls.error_threshold = error_threshold

    @property
    def engine(self):
        return self._chaos_executor.app

    def _filter_network_chaos_events(self):
        return {k: v for k, v in self._chaos_list.iteritems() if 'network' in k}

    def host_ip(self):
        return get_host_ip()

    def _parse_time_interval(self, time_interval):
        """
        Parse given time string expressed as <number>[s\m\h\d\w] to seconds
        where , s = seconds, m = minutes, h = hours, d = days, w = weeks
        e.g -> 1s = 1
               1m = 60
               1h = 3600
        :return:
        """
        if isinstance(time_interval, basestring):
            self.time_interval = float(
                time_interval[:-1]) * SECONDS_PER_TIME_UNIT[
                time_interval[-1]
            ]
        else:
            self.time_interval = float(time_interval)
