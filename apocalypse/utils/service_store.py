"""
@author: dhoomakethu

"""
from __future__ import absolute_import, unicode_literals
from apocalypse.utils.docker_client import docker_run, DockerClientException
from apocalypse.utils.logger import get_logger
from apocalypse.exceptions import NetError, UnknownServiceError

import re

chaos_logger = get_logger()
SERVICE_STATES = {
    # network
    "normal": "NORMAL",
    "delay": "NETWORK DELAY",
    "loss": "PACKET LOSS",
    "duplicate": "PACKET DUPLICATE",
    "corrupt": "PACKET CORRUPT",
    "reorder": "PACKET REORDERED",
    "blackhole": "NETWORK BLACKHOLE",

    # generic
    "stop_services": "SERVICE STOPPED",
    "reboot_services": "SERVICE REBOOTED",
    "terminate_services": "SERVICE TERMINATED",

    # resource
    "burn_cpu": "BURNING CPU",
    "burn_ram": "BURNING RAM",
    "kill_process": "KILLING RANDOM PROCESS"


}

EVENT_CATEGORY = {
    "stop_services": "generic",
    "reboot_services": "generic",
    "terminate_services": "generic",
    "burn_cpu": "resource",
    "burn_ram": "resource",
    "kill_process": "resource",
    "delay": "network",
    "loss": "network",
    "duplicate": "network",
    "corrupt": "network",
    "reorder": "network",
    "blackhole": "network",

}


def _create_service_map(ctrs):
    services = {}
    for k, v in ctrs.items():
        service = v["Name"].split("_")[1]
        v["Id"] = k
        services[service] = dict([("ctr_info", v),
                                  ("state", State("NORMAL"))])
    return services


def check_service(func):
    def _wrapper(self, service, *args, **kwargs):
        if service not in self.store.services:
            raise NetError("Unknown Service %s, check if the service is "
                           "running" % service)
        device = self._get_device(service)
        if not device:
            self.store.update_network_devices()
            # raise NetError("network interface for service %s could not be "
            #                "found" % service)
        return func(self, service, *args, **kwargs)
    return _wrapper


def update_service_state(func):
    def _wrapper(self, *args, **kwargs):
        services = args[0] if len(args) else kwargs.get('services')
        ret = func(self, *args, **kwargs)
        if ret:
            state = SERVICE_STATES.get(func.__name__)
            category = EVENT_CATEGORY.get(func.__name__)
            for service in services:
                self._update_service_state(service, category, state)
        return ret
    return _wrapper


class State(object):

    def __init__(self, init_state=None, dirty=True):
        self._state = {"network": [init_state],
                       "resource": [init_state],
                       "generic": [init_state]}
        self._dirty = dirty

    @property
    def state(self):
        return self._state

    def update(self, category, value, fresh=False):
        value = [value] if not isinstance(value, list) else value
        if fresh:
            self._state[category] = value
        else:
            if value not in self._state[category]:
                self._state[category].extend(value)

    def current_states(self):
        return list(set([x for v in self.state.values() for x in v]))

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    def __iter__(self):
        return iter(self.current_states())

    def __contains__(self, state):
        return state in self.current_states()

    def __len__(self):
        return len(self.current_states())


class ServiceStore(object):
    _services = {}
    _network_init = False

    def __init__(self, client, network):
        self.client = client
        self._network = network
        self.update_service_map()

    def get_device(self, service):
        chaos_logger.debug("Getting network interface for '%s'" % service)
        service_info = self._services.get(service, None)
        if service_info:
            return service_info.get("device", None)

    def update_network_devices(self):
        chaos_logger.debug("Getting network interfaces for containers")
        cmd = ["ip", "link"]
        host_res = docker_run(' '.join(cmd), client=self.client, stream=True)
        chaos_logger.debug("IP LINK \n %s" % host_res.decode('utf-8'))
        for service, val in self._services.items():
            chaos_logger.debug("Finding network interface for %s" % service)
            ctr = val['ctr_info']
            try:
                res = self.client.execute_command(
                    ctr, ['ip', 'link', 'show', 'eth0'], split_res=False,
                    stream=False, retry_on_error=False
                )
                if isinstance(res, (list, tuple)):
                    o, e = res
                    o = "".join(o) + "".join(e)
                    res = o
            except DockerClientException as e:
                res = e.message

            res = res.decode('utf-8')
            device = re.search('^([0-9]+):', res)
            if not device:
                chaos_logger.warning("Problem determining host device id"
                                     "for service '%s' - %s" % (service, res))
                self._services.pop(service)

            else:
                peer_idx = int(device.group(1))
                host_idx = peer_idx + 1
                host_rgx = '^%d: ([^:@]+)[:@]' % host_idx
                host_match = re.search(host_rgx, host_res, re.M)
                if not host_match:
                    chaos_logger.warning(
                        "Problem determining host network device "
                        "for service '%s' - %s, could not match host device "
                        "" % (service, res))
                    chaos_logger.debug(
                        "peer -id : %s , host_id: %s" % (peer_idx, host_idx)
                    )
                    self._services.pop(service)
                else:
                    host_device = host_match.group(1)
                    device = host_device  # NetworkDevice(host_device)
                    val['device'] = device

    def update_service_map(self):
        chaos_logger.debug("Creating Serving - container map")
        networks = self.client.list_networks()
        network = [netw for netw in networks if self._network in netw[
            'Name']]
        if not network:
            raise NetError("Network %s not found" % self._network)
        network = network[0]
        ctrs = network.get("Containers", {})
        self._services = _create_service_map(ctrs)

    def get_state(self, service):
        ser = self.get_service(service)
        x = ser['state'].current_states()
        chaos_logger.debug("Current network state for '%s' is '%s'" % (
            service, x))
        return x

    def get_services(self):
        return self._services

    def get_service(self, service):
        service_info = self.get_services().get(service)
        if not service_info:
            raise UnknownServiceError("Service '%s' not found, make sure the "
                                      "service is running " % service)
        return service_info

    def get_container_info(self, service):
        return self.get_service(service).get("ctr_info")

    @property
    def services(self):
        return self._services.keys()