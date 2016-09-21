"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
import os
from apocalypse.app import App
from apocalypse.exceptions import ServiceNotRunningError, handle_exception
from apocalypse.exceptions import NoServiceRunningError, NetError
from apocalypse.chaos.events.net import NetworkEmulator
from apocalypse.utils.service_store import (
    ServiceStore, update_service_state)
from apocalypse.utils.docker_client import DockerClient
from apocalypse.utils.logger import get_logger
from docker.errors import APIError

import random


logger = get_logger()
stress_exe = "/bin/stress"
tmp_loc = "/tmp"

curr_dir = os.path.dirname(__file__)
curr_dir = curr_dir.split(os.sep)[:-1]
stress_exe = os.sep.join(curr_dir)+stress_exe


# @HandleException(logger, NoServiceRunningError, NetError)
class ChaosApp(App):
    """
    Represents  Chaos app


    """
    _dirty_service = {}  # services stopped or terminated

    def __init__(self, network):
        super(ChaosApp, self).__init__(network)
        self._driver = DockerClient()
        self.init()

    @handle_exception(logger, "exit", NoServiceRunningError, NetError)
    def init(self):
        """
        creates an connection to compute engine
        """
        self._service_store = ServiceStore(self.driver, self.network)
        self._emulator = NetworkEmulator(self.store, self.driver)

    @handle_exception(logger, "exit", NoServiceRunningError, NetError)
    def init_network_emulator(self):
        logger.info("Initializing Network emulator")
        self.store.update_network_devices()
        # self.emulator.init()

    @update_service_state
    def stop_services(self, services):
        """
        stops a cloud instance
        """
        services = self._filter_cid(services)
        for service in services:
            ctr = self.check_service_running(service, raise_on=['terminated'])
            logger.info("Stopping docker instance : %s" % service)
            self.driver.stop_container(ctr['Id'])
            if service not in self._dirty_service:
                self._dirty_service[service] = {"ctr": ctr,
                                                "terminated": False}

        # self.store.update_service_map()
        return services

    @update_service_state
    def terminate_services(self, services):
        """
        terminates a cloud instance
        """
        services = self._filter_cid(services)
        for service in services:
            ctr = self.check_service_running(service,
                                             raise_on=['terminated'])
            logger.info("Stopping and "
                        "removing docker instance : %s" % service)
            self.driver.stop_container(ctr['Id'], remove=True)
            if service not in self._dirty_service:
                self._dirty_service[service] = {"ctr": ctr,
                                                "terminated": True}
            else:
                self._dirty_service[service]["terminated"] = True
        return services

    @update_service_state
    def kill_process(self, services, process, signal=9):
        services = self._filter_cid(services)
        for service in services:
            ctr = self.check_service_running(service)
            procs = self._get_running_processes(ctr["Id"])
            for proc in procs:
                try:
                    cmd = "kill -%s %s" % (signal, proc['pid'])
                    logger.info('killing random process {pid: %s, name: %s, '
                                'owner: %s} from cid %s' % (
                        proc['pid'], proc['name'], proc['user'], service))
                    self.driver.execute_command(ctr["Id"], cmd)

                except APIError as e:
                    logger.error('Docker error : %s' % e)
                    break
        return services

    @update_service_state
    def remote_kill_process(self, services, **kwargs):
        # process, signal, ssh, cmd, sudo
        super(ChaosApp, self).remote_kill_process(
            instance_ids=services, **kwargs)
        return services

    @update_service_state
    def stop_upstart_job(self, services, **kwargs):
        #  ssh, job, cmd,
        super(ChaosApp, self).stop_upstart_job(instance_ids=services,
                                               **kwargs)
        return services

    @update_service_state
    def stop_initd_job(self, services, **kwargs):
        # ssh, job, cmd
        super(ChaosApp, self).stop_initd_job(instance_ids=services,
                                             **kwargs)
        return services

    @update_service_state
    def reboot_services(self, services):
        remove = False
        services = self._filter_cid(services)
        for service in services:
            ctr = self.check_service_running(service, ["terminated"])
            logger.info("Rebooting docker container %s " % service)
            self.driver.restart_container(ctr["Id"])
            if remove:
                self._dirty_service.pop(service)
        return services

    @update_service_state
    def burn_cpu(self, services, cpuload, duration, cpu_core):
        services = self._filter_cid(services)
        t = tmp_loc + "/" + os.path.basename(stress_exe)
        access_cmd = "chmod 755 %s" % t
        cmd = ("%s cpu --cpuload %s"
               " --duration %s"
               " --cpucore %s" % (t,
                                  cpuload,
                                  duration,
                                  cpu_core
                                  )
               )
        for service in services:
            ctr = self.check_service_running(service)
            logger.info("Setting CPU load to %s "
                        "for %s Seconds on "
                        "container %s" % (cpuload, duration, service))
            # self._copy_to_container(ctr, stress_exe, tmp_loc)
            self.driver.copy_to_container(ctr, stress_exe, tmp_loc)
            self.driver.execute_command(ctr, access_cmd)
            self.driver.execute_command(ctr, cmd)
        return services

    @update_service_state
    def burn_ram(self, services, ramload, duration):
        services = self._filter_cid(services)
        t = tmp_loc + "/" + os.path.basename(stress_exe)
        access_cmd = "chmod 755 %s" % t
        cmd = ("%s ram --ramload %s"
               " --duration %s" % (t, ramload, duration))
        for service in services:
            ctr = self.check_service_running(service)
            logger.info("Setting RAM load to %s "
                        "for %s Seconds on "
                        "container %s" % (ramload, duration, service))
            self.driver.copy_to_container(ctr, stress_exe, tmp_loc)
            result = self.driver.execute_command(ctr, access_cmd)
            logger.debug(result)
            result = self.driver.execute_command(ctr, cmd)
            logger.debug(result)

        return services

    @update_service_state
    def burn_io(self, services, **kwargs):
        services = self._filter_cid(services)
        super(ChaosApp, self).burn_io(instance_ids=services)
        return services

    @update_service_state
    def burn_disk(self, services, **kwargs):
        # instance_ids, size, path, duration
        services = self._filter_cid(services)
        super(ChaosApp, self).burn_disk(instance_ids=services, **kwargs)
        return services

    def network_loss(self, services, **kwargs):
        """
        {
            loss: 5%,
            correlation: 25
        }

        :param service:
        :param kwargs:
        :return:
        """
        for service in services:
            self.check_service_running(service)
            logger.info("Simulating network loss on %s with %s" % (service,
                                                                   kwargs))
            self.emulator.loss(service, **kwargs)
        return services

    def network_blackout(self, services):
        for service in services:
            logger.info("Simulating network blackout on %s " % service)
            self.check_service_running(service)
            self.emulator.blackhole(service)
        return services

    def network_corrupt(self, services, **kwargs):
        for service in services:
            logger.info("Simulating network packet corruption "
                        "on %s with %s" % (service, kwargs))
            self.check_service_running(service)
            self.emulator.corrupt(service, **kwargs)
        return services

    def network_duplicate(self, services, **kwargs):
        for service in services:
            logger.info("Simulating network packet duplication "
                        "on %s with %s" % (service, kwargs))
            self.check_service_running(service)
            self.emulator.duplicate(service, **kwargs)
        return services

    def network_delay(self, services, **kwargs):
        """
        {
            "service": "userservice",
            "event": {
                "jitter": "100ms",
                "delay": "1s",
                "distribution": "normal"
            }
        }
        :param client:
        :param services:
        :param params:
        :param kwargs:
        :return:
        """
        for service in services:
            logger.info("Simulating network delay "
                        "on %s with %s" % (service, kwargs))
            self.check_service_running(service)
            self.emulator.delay(service, **kwargs)
        return services

    def network_reorder(self,  services, **kwargs):
        for service in services:
            logger.info("Simulating network packet reorder "
                        "on %s with %s" % (service, kwargs))
            self.check_service_running(service)
            self.emulator.reorder(service, **kwargs)
        return services

    def get_services(self):
        services = self.store.services
        return services

    def get_service_state(self, service):
        return self.store.get_state(service)

    def choice(self, services=None, event=None):
        """
        choose a random vm
        """
        external = ['redis', 'etcd', 'cassandra', 'registrator']
        exclude = ['killprocesses', 'burncpu', 'burnram', 'burndisk', 'burnio']
        if services:
            if isinstance(services, (list, tuple)):
                _services = list(set(services) & set(self.get_services()))
                # for _service in services:
                #     for ctr in self.get_services():
                #         if _service in ctr['Name'] or _service in ctr['Id']:
                #             _services.append(ctr)
                if _services:
                    return _services
            else:
                # for ctr in self.get_services().items():
                #     if services in ctr['Name'] or services in ctr['Id']:
                #         return ctr
                return list(set([services]) & set(self.get_services()))
            logger.info("Docker containers '%s' is "
                        "not running/found!!!" % (services,))
            return None
        if event is not None and event.lower() in exclude:
            _services = [service for service in self.get_services()
                         if not any(exclude == service
                                    for exclude in external)]
            if not _services:
                logger.info("No docker services running!!!")
                vm = None
            else:
                vm = random.choice(_services)
        else:
            services = self.get_services()
            if self.get_services():
                vm = random.choice(services)
                logger.info("Picking random docker container %s " % vm)
            else:
                logger.info("No docker containers running!!!")
                vm = None

        return vm

    def __repr__(self):
        return '%s' % self.__class__.__name__

    def _get_running_processes(self, cid):
        cmd = "ps aux"
        resp = self.driver.execute_command(cid, cmd)
        header = resp[0].split()
        pid_col = 0
        user_col = 1
        cmd_col = 2
        if len(header) > 4:
            for i, col in enumerate(header):
                if "pid" in col.lower():
                    pid_col = i
                elif "user" in col.lower():
                    user_col = i
                elif "command" in col.lower():
                    cmd_col = i

        columns = len(header) - 1
        procs = []
        for r in resp[1:]:
            cols = r.split(None, columns)
            if len(cols) >= max(pid_col, user_col, cmd_col):
                pid, user, name = cols[pid_col], cols[user_col], cols[cmd_col]
                if name != cmd:
                    procs.append({'pid': pid, 'user': user, 'name': name})

        return procs

    def _filter_cid(self, cids):
        """
        Filters container ID's to work with only running containers
        """
        return [cid for cid in cids if cid is not None]

    def _update_service_state(self, service, category, state):
        service_info = self.store.get_service(service)
        service_state = service_info.get("state")
        if state not in service_state:
            service_state.update(category, state)

    def get_controller_attr(self, ctr, port_dict, scheme_dict):
        ctr_name = self.driver.get_container_info(ctr, 'Name')
        combined_dict = {}
        for (service1, port), (service2, scheme) in zip(port_dict.items(), scheme_dict.items()):
            if service1 in ctr_name:
                combined_dict[ctr_name] = [port, scheme]

        return combined_dict, ctr_name

    def check_service_running(self, service,
                              raise_on=["terminated", "stopped"]):
        if service in self._dirty_service:
            dirty_info = self._dirty_service.get(service)
            ctr = self._dirty_service.get(service).get("ctr")
            state = "stopped"
            if dirty_info.get("terminated"):
                state = "terminated"
            if state in raise_on:
                raise ServiceNotRunningError("Service %s "
                                             "is %s" % (service, state))

            return ctr
        return self.store.get_container_info(service)