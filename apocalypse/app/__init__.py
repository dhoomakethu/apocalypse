"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

from abc import ABCMeta, abstractmethod


class App(object):

    __metaclass__ = ABCMeta

    _driver = None
    _service_store = None
    _emulator = None

    def __init__(self, network):
        # self._network = getattr(Provider, network)
        # self.compute_engine = get_driver(self._network)
        self._network = network

    @property
    def driver(self):
        return self._driver

    @property
    def store(self):
        return self._service_store

    @property
    def network(self):
        return self._network

    @property
    def emulator(self):
        return self._emulator

    @abstractmethod
    def choice(self):
        """
        choose a random vm
        """
    # @abstractmethod
    # def connect(self):
    #     """
    #     creates an connection to compute engine
    #     """
    @abstractmethod
    def stop_services(self, **kwargs):
        """
        stops a cloud instance
        """

    @abstractmethod
    def terminate_services(self, **kwargs):
        """
        terminates a cloud instance
        """

    @abstractmethod
    def reboot_services(self, **kwargs):
        """
        reboots the instance
        """

    @abstractmethod
    def kill_process(self, **kwargs):
        """
        kills a process from the instance
        """

    @abstractmethod
    def remote_kill_process(self, **kwargs):
        """
        kills a process runnning in a remote instance
        """

    @abstractmethod
    def stop_upstart_job(self, **kwargs):
        """
        stops an upstart job

        """

    @abstractmethod
    def stop_initd_job(self, **kwargs):
        """
        stops an initd job

        """

    @abstractmethod
    def burn_cpu(self, **kwargs):
        """
        Loads CPU core to desired load percentage
        Args:
            instance_ids:
            cpuload:
            duration:
            cpucore:

        Returns:

        """

    @abstractmethod
    def burn_ram(self, **kwargs):
        """
        Stress RAM with desired load
        Args:
            instance_ids:
            ramload:
            duration:

        Returns:

        """

    @abstractmethod
    def burn_io(self, **kwargs):
        """
        Stress IO
        Args:
            instance_ids:

        Returns:

        """

    @abstractmethod
    def burn_disk(self, **kwargs):
        """
        Stress DISK
        Args:
            instance_ids:
            size:
            path:
            duration:

        Returns:

        """

    @abstractmethod
    def network_blackout(self, **kwargs):
        """
        Simulates Network blackout on a container

        Returns:

        """

    @abstractmethod
    def network_corrupt(self, **kwargs):
        """
        Corrupts random network packets for the given service

        Returns:

        """

    @abstractmethod
    def network_loss(self, **kwargs):
        """
        drop random network packets

        Returns:

        """

    @abstractmethod
    def network_duplicate(self, **kwargs):
        """
        Duplicates network packets

        Returns:

        """

    @abstractmethod
    def network_delay(self, **kwargs):
        """
        Simulates delay with network transactions

        Returns:

        """

    @abstractmethod
    def network_reorder(self, **kwargs):
        """
        Reorders a given percent of network packets

        Returns:

        """
