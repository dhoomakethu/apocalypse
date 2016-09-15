"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

from apocalypse.utils.logger import get_logger

from apocalypse.chaos import register
from apocalypse.chaos import ChaosEvent
from apocalypse.chaos.executor import ChaosExecutor

chaos_logger = get_logger()

__all__ = ["NetworkCorrupt", "NetworkDelay", "NetworkBlackout",
           "NetworkLoss", "NetworkDuplicate", "NetworkReorder"]


@register(ChaosExecutor)
class NetworkBlackout(ChaosEvent):
    # Reads the packets that have been sent then hangs.
    enabled = True
    _category = "network"

    def _network_blackout(self):

        vm = self._prepare('NetworkBlackout')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_blackout(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_blackout()


@register(ChaosExecutor)
class NetworkDelay(ChaosEvent):
    # Adds a delay before or after the backend is called.
    enabled = True
    _category = "network"

    options = {
        'delay': [
            "Delay in terms of seconds (ms/ns/s) (float)",
            str,
            "1s"
        ],
        'jitter': [
            "If True adds before the backend is called. Otherwise after",
            str,
            '100ms'
        ],
        'distribution': [
            "delay distribution",
            str,
            "Normal"
        ]
    }

    def _network_delay(self):

        vm = self._prepare('NetworkDelay')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_delay(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_delay()


@register(ChaosExecutor)
class NetworkCorrupt(ChaosEvent):
    enabled = True
    _category = "network"

    options = {
        'corrupt': [
            "random packet corruption percentage",
            str,
            "10%"
        ],
        'correlation': [
            "correlation percentage",
            str,
            "25%"
        ]
    }

    def _network_corrupt(self):
        vm = self._prepare('NetworkCorrupt')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_corrupt(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_corrupt()


@register(ChaosExecutor)
class NetworkLoss(ChaosEvent):
    enabled = True
    _category = "network"

    options = {
        'loss': [
            "random packet loss percentage",
            str,
            "10%"
        ],
        'correlation': [
            "correlation percentage",
            str,
            "25%"
        ]
    }

    def _network_loss(self):
        vm = self._prepare('NetworkLoss')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_loss(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_loss()


@register(ChaosExecutor)
class NetworkDuplicate(ChaosEvent):
    enabled = True
    _category = "network"

    options = {
        'duplicate': [
            "random packet duplicate percentage",
            str,
            "10%"
        ],
        'correlation': [
            "correlation percentage",
            str,
            "25%"
        ]
    }

    def _network_duplicate(self):
        vm = self._prepare('NetworkDuplicate')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_duplicate(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_duplicate()


@register(ChaosExecutor)
class NetworkReorder(ChaosEvent):
    enabled = True
    _category = "network"

    options = {
        'delay': [
            "Delay in terms of seconds (ms/ns/s) (float)",
            str,
            "1s"
        ],
        'reorder': [
            "random packet reorder percentage",
            str,
            "10%"
        ],
        'correlation': [
            "correlation percentage",
            str,
            "25%"
        ],
        'gap': [
            "number of packets to be delayed",
            int,
            5
        ],
    }

    def _network_reorder(self):
        vm = self._prepare('NetworkReorder')
        vm = vm if isinstance(vm, (list, tuple)) else [vm]
        return self.app.network_reorder(vm, **self.options)

    def __call__(self, driver, **kwargs):
        self.app = driver
        self.services = kwargs.pop("services", [])
        self.options = kwargs
        return self._network_reorder()
