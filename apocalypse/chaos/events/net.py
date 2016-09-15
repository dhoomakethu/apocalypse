"""
@author: dhoomakethu

Largely inspired by blockade, adapted as per our needs

https://github.com/dcm-oss/blockade

"""
from apocalypse.utils.docker_client import DockerClient, docker_run
from apocalypse.utils.logger import get_logger
from apocalypse.utils.service_store import check_service

IPTABLES_DOCKER_IMAGE = "vimagick/iptables:latest"

NETWORKSTATE = {
    "normal": "NORMAL",
    "delay": "SLOW",
    "loss": "LOSS",
    "duplicate": "DUPLICATE",
    "corrupt": "CORRUPT",
    "reorder": "REORDERED",
    "blackhole": "BLACKHOLE"
}

chaos_logger = get_logger()


def _filter_network_state(states):
    if len(states) > 1:
        return [state for state in states if state != NETWORKSTATE["normal"]]
    else:
        return states.current_states()


def _tc_restore(client, device):
    cmd = ["tc", "qdisc", "del", "dev", device, "root"]
    return docker_run(' '.join(cmd), client=client)


def _restore_other_nw_state(client, device):
    cmd = "ifconfig %s up" % device
    resp = docker_run(cmd, client=client)
    return resp


def _create_blackhole(client, device,):
    cmd = "ifconfig {} down".format(device)
    resp = docker_run(cmd, client=client)
    return resp


def _tc_netem(client, device, params):
    cmd = ["tc", "qdisc", "replace", "dev", device,
           "root", "netem"] + params
    resp = docker_run(' '.join(cmd), client=client)
    return resp


def _tc_network_state(client, device):
    cmd = ["tc", "qdisc", "show", "dev", device]
    output = docker_run(' '.join(cmd), client=client)
    states = tuple(set(output.split()) & set(NETWORKSTATE.keys()))
    states = [NETWORKSTATE[state] for state in states]
    # return "-".join(states) if states else NETWORKSTATE['normal']
    return states if states else [NETWORKSTATE['normal']]


def _other_network_state(client, device):
    cmd = ["ip", "link", "show", device]
    output =docker_run(' '.join(cmd), client=client)
    if "state DOWN" in output:
        return [NETWORKSTATE['blackhole']]
    elif "state UP" in output:
        return [NETWORKSTATE['normal']]
    else:
        return [NETWORKSTATE['normal']]


OTHER_RESTORE_MAP = {"BLACKHOLE": _restore_other_nw_state}
TC_RESTORE_MAP = {state: _tc_restore for state in NETWORKSTATE.values() if
                  state not in OTHER_RESTORE_MAP.keys()}


class NetworkEmulator(object):
    """
    Class to emulate network events using linux utils 'tc', 'iptables' and
    'ip route'

    """
    client = None
    _dirty = False
    _store = None

    def __init__(self, store, client=None):
        self.client = DockerClient() if not client else client
        self._store = store

    def _get_device(self, service):
        return self.store.get_device(service)

    def _init_states(self):
        for service, info in self.get_services().items():
            chaos_logger.debug("initializing state for %s" % service)
            # print "initializing state for %s" % service
            self._init_state(info)

    def _init_state(self, service_info):
        states = []
        # device = service_info.get("device").device
        device = service_info.get("device")
        chaos_logger.debug("getting tc state")
        states.extend(_tc_network_state(self.client, device))
        chaos_logger.debug("getting ifconfig")
        states.extend(_other_network_state(self.client, device))
        # print "done"
        states = list(set(states))
        service_info['state'].update("network", states, fresh=True)
        # service_info['device'].state = states

    def init(self, service=None):
        chaos_logger.debug("Initializing Network emulator")
        if service:
            service_info = self.get_services().get(service)
            self._init_state(service_info)
        else:
            self._init_states()

    @property
    def store(self):
        return self._store

    def get_services(self):
        return self.store.get_services()
    
    def delay(self, service, **kwargs):
        """
        adds the chosen delay to the packets outgoing to chosen network
           interface. The optional parameters allows to introduce a delay
           variation and a correlation.  Delay and jitter values are expressed
           in ms while correlation is percentage.
        :param client:
        :param kwargs:
        :return:
        """
        # device = kwargs.pop('device')
        kwargs = {k: str(v).lower() for k, v in kwargs.items()}
        chaos_logger.debug("Emulating 'Delay' for service-'%s'" % service)
        cmd = ("delay {delay} {jitter} distribution {distribution}".format(
            **kwargs))
        return self.emulate_network(service, "delay", cmd.split())

    def loss(self, service, **kwargs):
        """
        adds an independent loss probability to the packets outgoing from the
           chosen network interface
        :param client:
        :param kwargs:
        :return:
        """
        chaos_logger.debug("Emulating 'Packet Loss' for service-'%s'" %
                           service)
        cmd = "loss {loss} ".format(**kwargs)
        cmd += "{}".format(kwargs.get("correlation", ""))
        return self.emulate_network(service, "loss", cmd.split())

    def corrupt(self, service, **kwargs):
        """
        allows the emulation of random noise introducing an error in a random
           position for a chosen percent of packets. It is also possible to
           add a correlation through the proper parameter.

        :param client:
        :param kwargs:
        :return:
        """
        chaos_logger.debug("Emulating 'Network Corrupt' for service-'%s'" %
                           service)
        cmd = "corrupt {corrupt} ".format(**kwargs)
        cmd += "{}".format(kwargs.get("correlation", ""))
        return self.emulate_network(service, "corrupt", cmd.split())

    def duplicate(self, service, **kwargs):
        """
        using this option the chosen percent of packets is duplicated before
           queuing them. It is also possible to add a correlation through the
           proper parameter
        :param client:
        :param kwargs:
        :return:
        """
        chaos_logger.debug("Emulating 'Duplication of packets' for "
                           "service-'%s'" % service)
        cmd = "duplicate {duplicate} ".format(**kwargs)
        cmd += "{}".format(kwargs.get("correlation", ""))
        return self.emulate_network(service, "duplicate", cmd.split())

    def reorder(self, service, **kwargs):
        """
        reorders the packets to be sent , to use reordering, a delay option
        must be specified
        tc qdisc change dev eth2 root netem delay 10ms reorder 25% 50%
        In this example, 25% of packets (with a correlation of 50%) will get
        sent  immediately, others will be delayed by 10ms.
        :param client: docker client
        :param kwargs: args to be supplied to tc command
        :return:
        """
        chaos_logger.debug("Emulating 'Reording of packets' for "
                           "service-'%s'" %
                           service)
        cmd = "delay {delay} reorder {reorder} ".format(**kwargs)
        gap = kwargs.get("gap", "")
        cmd += "{} ".format(kwargs.get("correlation", ""))
        cmd += "gap {}".format(gap) if gap else ""
        return self.emulate_network(service, "reorder", cmd.split())

    def blackhole(self, service):
        """
        packet matching a route with the route type blackhole is discarded.
        No ICMP is sent and no packet is forwarded.

            Many ways to achieve this
            1 .use ip route add blackhole <ip of the container> -> does not
            work unless entire subnet is added
            2. remove container from network -> works just fine but requires
            container restart to get back to normal shape
            3. scale down service docker-compose scale <service>=0 --> Best
            option
             restart with ./minicloud restart service
            4. disabale netork interface

        :param client:
        :param service: service to be made unavailable
        :return:
        """
        chaos_logger.debug("Emulating 'Blackhole' "
                           "for service-'%s'" % service)
        # device = self._get_device(service)
        service_info = self.get_services().get(service)
        device_state = service_info.get("state")
        device = service_info.get("device")
        resp = _create_blackhole(self.client, device)
        if not resp:
            if NETWORKSTATE.get("blackhole") not in device_state:
                device_state.update("network", NETWORKSTATE.get("blackhole"))

        return resp

    def faildns(self):
        """
        # Block all traffic on port 53

        iptables -A INPUT -p tcp -m tcp --dport 53 -j DROP
        iptables -A INPUT -p udp -m udp --dport 53 -j DROP

        For example, if you want to delete the rule

        sudo iptables -D INPUT -p tcp -m tcp --dport 53 -j DROP
        sudo iptables -D INPUT -p udp -m udp --dport 53 -j DROP

        :return:
        """
        pass

    @check_service
    def restore(self, service):
        chaos_logger.debug("Restoting service-'%s'"
                           " back to 'NORMAL'" % service)
        resp = []
        service_info = self.get_services().get(service)
        device_state = service_info.get("state")
        device = service_info.get("device")
        current_states = [state for state in device_state
                          if state != "NORMAL"]
        for state in current_states:
            device_state.dirty = True
            if state in TC_RESTORE_MAP:
                resp.append(TC_RESTORE_MAP[state](self.client, device))
            elif state in OTHER_RESTORE_MAP:
                resp.append(OTHER_RESTORE_MAP[state](self.client,
                                                     device))
            else:
                chaos_logger.debug("Unknown network state %s " % state)

        return resp

    @check_service
    def emulate_network(self, service, event, params):
        # device = self._get_device(service)
        service_info = self.get_services().get(service)
        device_state = service_info.get("state")
        device = service_info.get("device")
        resp = _tc_netem(self.client, device, params)
        if not resp:
            if NETWORKSTATE.get(event) not in device_state:
                device_state.update("network", NETWORKSTATE.get(event))

        return resp

    @check_service
    def network_state(self, service):
        chaos_logger.debug("Getting current network state for %s" % service)
        service_info = self.get_services().get(service)
        device_state = service_info.get("state")

        if device_state.dirty or not device_state.state:
            self.init(service)
            device_state.dirty = False

        return _filter_network_state(device_state)

