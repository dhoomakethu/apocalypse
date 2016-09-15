"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

import re

from apocalypse.utils.logger import get_logger

from apocalypse.chaos import register
from apocalypse.chaos import ChaosEvent
from apocalypse.chaos.executor import ChaosExecutor

pid_regexp = re.compile(r"^\d+$")

chaos_logger = get_logger()

__all__ = ["BurnCpu", "BurnDisk", "BurnIO", "BurnRAM"]


@register(ChaosExecutor)
class BurnCpu(ChaosEvent):
    enabled = True
    _category = "resource"
    options = {
        'load': [
            "cpu target load 0<cpuload<1",
            float,
            0.5
        ],
        'duration': [
            'duration for which CPU load to be performed in seconds '
            '-1 represent run forever',
            float,
            10
        ],
        'cores': [
            'cpu cores to load (ignored)',
            int,
            0
        ],

        }

    def _burn_cpu(self):
        vm = self._prepare('BurnCpu')
        return self.app.burn_cpu(
                services=vm if isinstance(vm, (list, tuple)) else [vm],
                cpuload=self.cpuload,
                duration=self.duration,
                cpu_core=self.cpu_core
        )

    def __call__(self, driver,
                 load=0.5, duration=10, cores=0, services=None):
        self.app = driver
        self.services = services
        self.cpuload = load
        self.duration = duration
        self.cpu_core = cores
        return self._burn_cpu()


@register(ChaosExecutor)
class BurnIO(ChaosEvent):
    enabled = False
    _category = "resource"

    def _burn_io(self):
        cmd = ""
        vm = self._prepare('BurnIO')

        return self.app.burn_io(
            services=vm if isinstance(vm, (list, tuple)) else [vm],
            cmd=cmd
        )

    def __call__(self, driver, *args, **kwargs):
        self.app = driver
        self.services = kwargs.get('services', None)
        return self._burn_io()


@register(ChaosExecutor)
class BurnRAM(ChaosEvent):
    enabled = True
    _category = "resource"
    options = {
        'load': [
            "ram target load 0<cpuload<1",
            float,
            0.5
        ],
        'duration': [
            'duration for which RAM load to be performed in seconds, '
            '-1 represent run forever',
            float,
            10
        ],

    }

    def _burn_ram(self):
        vm = self._prepare(event='BurnRam')
        return self.app.burn_ram(
            services=vm if isinstance(vm, (list, tuple)) else [vm],
            ramload=self.ramload,
            duration=self.duration
        )

    def __call__(self, driver, load=0.5, duration=10, services=None):
        self.app = driver
        self.services = services
        self.ramload = load
        self.duration = duration
        return self._burn_ram()


@register(ChaosExecutor)
class BurnDisk(ChaosEvent):
    enabled = False
    _category = "resource"

    def _burn_disk(self):
        cmd = ""
        vm = self._prepare('BurnDisk')
        return self.app.burn_disk(
            services=vm if isinstance(vm, (list, tuple)) else [vm],
            cmd=cmd
        )

    def __call__(self, driver, *args, **kwargs):
        self.app = driver
        self.services = kwargs.get('services', None)
        return self._burn_disk()
