"""
@author: dhoomakethu
"""
from __future__ import unicode_literals
from __future__ import absolute_import
import docker
import os
import atexit
import json
import pprint
import time
import requests
import platform
import tarfile
from io import BytesIO
from apocalypse.utils.proc import Proc,  MessageNotFound
from apocalypse.utils.logger import get_logger
from docker.errors import APIError, NotFound
from requests.exceptions import ConnectionError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


_NOT_SET = object()

log = get_logger()
IPTABLES_DOCKER_IMAGE = "vimagick/iptables:latest"


class DockerClientException(Exception):
    """
    Docker client execption
    """
    pass


def which(program):
    """
    Checks if executable exists and is on the path.
    Thanks http://stackoverflow.com/a/377028/119592
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
          return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def get_host_ip():
    cmd = ("ifconfig | grep 'inet' | grep -v 'inet6\|127' | "
           "head -n 1 | tr -d [a-z:] | awk '{print $1}'")

    p = Proc(cmd, shell=True)
    p.run()
    ip, err = p.proc_output()
    if err:
        raise "\n".join(err)
    if ip:
        ip = ip[0].strip("\n")

    return ip


def get_host():
    return platform.system()


def docker_run(command, image='ubuntu:trusty', network_mode='host',
               privileged=True, client=None, stream=False):
    """
    # copied from blockade with minor enhancements
    Runs the command on the docker container with provided image and returns
    logs

    Args:
        command: non blocking command to be run
        image: Docker image to create container with
        network_mode: network mode for container
        privileged: True/False
        client: docker client
        stream: True/False stream docker logs from container

    Returns:

    """
    docker_client = DockerClient() if not client else client
    host_config = docker_client.create_host_config(
        network_mode=network_mode, privileged=privileged)
    try:
        container = docker_client.create_container(image=image,
                                                   command=command,
                                                   host_config=host_config)
    except docker.errors.NotFound:
        docker_client.pull(image)

        container = docker_client.create_container(image=image,
                                                   command=command,
                                                   host_config=host_config)

    docker_client.start_container(container)

    stdout = docker_client.get_logs(container,
                                    stdout=True, stream=stream)
    if stream:
        output = b''
        for item in stdout:
            output += item

    output = output.decode('utf-8') if stream else stdout.decode('utf-8')

    status_code = docker_client.wait_till_stopped(container)
    docker_client.remove_container(container, force=True)
    if status_code == 2 and 'No such file or directory' in output:
        # docker_client.remove_container(container, force=True)
        return
    elif status_code != 0:
        err_msg = "Problem running command '%s' - %s" % (command, output)
        log.debug(err_msg)
        raise DockerClientException(err_msg)

    # if isinstance(docker_client, docker.Client):
    #     docker_client.remove_container(container=container.get('Id'),
    #                                    force=True)
    # else:
    #     docker_client.remove_container(cid=container, force=True)
    log.debug("Succesfully ran command - %s" % command)
    return output


class DockerClient(object):
    """
    Wrapper class around docker.client.Client() class

    """
    def __init__(self, **kwargs):
        self.client = None
        self.init(**kwargs)
    
    def init(self, **kwargs):
        self.client = docker.Client(**kwargs)
        try:
            log.debug("Client info :\n%s", pprint.pformat(self.client.info()))
        except ConnectionError as e:
            log.exception('Unable to connect to docker, '
                          'cannot use docker for running tests')
            log.exception('Check value of DOCKER_HOST, DOCKER_TLS_VERIFY, '
                          'and DOCKER_CERT_PATH environment variables')
            raise EnvironmentError(e)

    def create_container(self, image, **kwargs):
        ctr = self.client.create_container(image, **kwargs)
        return ctr

    def find_container(self, by, key, all=False):
        by = "names" if by == 'name' else by
        containers = self.client.containers(all=all)
        if key:
            ctr = None
            if containers:
                for c in containers:
                    if ctr:
                        break
                    if isinstance(c[by.capitalize()], (tuple, list)):
                        if by is not "names":
                            for val in c[by.capitalize()]:
                                if key in val:
                                    ctr = c
                                    break
                        else:
                            if key in c[by.capitalize()][0]:
                                ctr = c
                                break
                    else:
                        ctr = c if key in c[by.capitalize()] else None
            return ctr

    def find_container_by_id(self, ctr_id, all=False):
        return self.find_container("id", ctr_id, all)

    def find_container_by_name(self, ctr_name, all=False):
        return self.find_container("name", ctr_name, all)

    def find_container_by_image(self, ctr_image, all=False):
        return self.find_container("image", ctr_image, all)

    def inspect_container(self, container):
        log.debug("inspecting container %s" % container)
        return self.client.inspect_container(container)

    def get_container_info(self, container, info):
        inspect_info = self.inspect_container(container)
        for k, v in inspect_info.iteritems():
            if k.lower() == info.lower():
                if v:
                    return v
            else:
                if isinstance(v, dict):
                    for k1, v1 in v.iteritems():
                        if k1.lower() == info.lower():
                            if v1:
                                return v1
        return None

    def get_container_ip(self, ctr, network=None):
        inspect_info = self.inspect_container(ctr)
        ntwrks = self.client.networks()
        network = [ntwrk['Name'] for ntwrk in ntwrks if ntwrk['Id'] == network['Id']]
        ipaddress = ''
        network_settings = inspect_info['NetworkSettings']
        if network:
            networks = network_settings['Networks'].get(network[0], None)
            if networks:
                ipaddress = networks[u'IPAddress']
        else:
            ipaddress = network_settings[u'IPAddress']

        return ipaddress

    def create_host_config(self, **kwargs):
        host_config = self.client.create_host_config(**kwargs)
        return host_config

    def get_containers(self, all=True, info=['Names', 'Id'], **kwargs):
        containers = self.client.containers(all=all, **kwargs)
        keys = containers[0].keys() if containers else ['Names', 'Id']
        if not isinstance(info, (list, tuple)):
            return containers
        else:
            keys = list(set(keys)&set(info))
            return [{k: v for k, v in ctr.iteritems()
                    if k in keys} for ctr in containers]

    def _wait_for_log_entry(self, cid, wait_for, timeout):
        success = False
        if wait_for is not None:
            while timeout > 0:
                gen = self.get_logs(cid, stream=True)
                for line in gen:
                    if wait_for in line:
                        success = True
                        break
                time.sleep(1)
                timeout -= 1
        else:
            success = True

        return success

    def start_container(self, cid, wait_for=None, clean_up=False, timeout=10,
                        **kwargs):
        self.client.start(cid, **kwargs)
        success = True
        if wait_for is not None:
            success = self._wait_for_log_entry(cid, wait_for, timeout)
        if not success:
            raise MessageNotFound("Error starting container , "
                                  "expected message not found in docker "
                                  "logs\n %s" % wait_for)
        if clean_up:
            atexit.register(self.stop_container, cid, clean_up)

    def stop_container(self, cid, remove=False):
        log.debug("Stopping container %s" % cid)
        try:
            self.client.stop(cid)
            if remove:
                self.remove_container(cid)
        except NotFound:
            log.debug("Container %s not found" % cid)

    def restart_container(self, cid, wait_for=None, clean_up=False, timeout=10,
                        **kwargs):
        log.debug("Restarting container %s " % cid)
        success = True
        self.client.restart(cid, **kwargs)
        if wait_for is not None:
            success = self._wait_for_log_entry(cid, wait_for, timeout)
        if not success:
            raise MessageNotFound("Error re-starting container ,"
                                  " expected message not found "
                                  "in docker logs\n %s" % wait_for)

    def remove_container(self, cid, **kwargs):
        log.debug("Removing container %s" % cid)
        self.client.remove_container(cid, **kwargs)

    def execute_command(self, cid, cmd, split_res=True, seperator='\n',
                        wait_for=None, stream=True, retry_on_error=True):
        log.debug("Executing command %s in container %s" % (cmd, cid))
        try:
            exc = self.client.exec_create(cid, cmd)
            resp = self.client.exec_start(exc, stream=stream)
            # 'SE:BW Connect Error Network Error : dial tcp: missing address'

            if split_res:
                result = []
                for r in resp:
                    result.extend(r.split(seperator))
                    if wait_for is not None and wait_for in r:
                        break
                return result

            else:
                return resp
        except APIError as e:
            log.critical(e)
            if retry_on_error:
                return self.execute_command_2(cid, cmd,
                                              split_res, seperator, wait_for)
            raise DockerClientException(e.explanation)

    def execute_command_2(self, cid, cmd, split_res=True, seperator='\n',
                          wait_for=None, retry=0, timeout=5):
        if isinstance(cmd, (list, tuple)):
            cmd = " ".join(cmd)
        cmd = ['docker', 'exec', cid['Id'], 'sh', '-c', cmd]
        p = Proc(cmd)
        retry = retry+1 if retry > 0 else 1
        while retry:
            try:
                p.run(wait_for=wait_for, timeout=timeout)
                break
            except MessageNotFound:
                if not retry-1:
                    raise
                retry -= 1
        return p.proc_output()

    def get_logs(self, ctr, stdout=True, stderr=True, stream=False,
                 timestamps=False, tail='all'):
        log.debug("Getting logs for %s" % ctr)
        return self.client.logs(ctr, stdout, stderr,
                                stream, timestamps, tail)

    def wait_till_stopped(self, ctr, timeout=None):
        log.debug("Waitng for container to stop %s" % ctr)
        return self.client.wait(ctr, timeout)

    @staticmethod
    def get_container_name(container):
        if not container.get('Name') and not container.get('Names'):
            return None
        # inspect
        if 'Name' in container:
            return container['Name']
        # ps
        shortest_name = min(container['Names'],
                            key=lambda n: len(n.split('/')))
        return shortest_name.split('/')[-1]

    def pull_image(self, image):
        not_found = True
        images = self.client.images()

        for img in images:
            if image in img['RepoTags']:
                not_found = False
                break
        if not_found:
            for line in self.client.pull(image, stream=True):
                log.debug(json.dumps(json.loads(line), indent=4))

    def port(self, container, priv_port=None):
        if isinstance(container, dict):
            container = self.get_container_info(container, "Id")
        cmd = ['docker', 'port', container]
        if priv_port:
            cmd.append(str(priv_port))
        p = Proc(cmd)
        p.run(timeout=3)
        out, err = p.proc_output()
        if err:
            raise EnvironmentError("\n".join(err))
        ports = []
        for port_info in out:
            if not priv_port:
                p = port_info.split('->')
                exposed_port, proto = p[0].split('/')
                host_ip, host_port = p[1].split(':')
                ports.append({'proto': proto,
                              'exposed_port': exposed_port,
                              'host_ip': host_ip,
                              'host_port': host_port})
            else:
                host_ip, host_port = port_info.split(':')
                ports.append({'host_ip': host_ip,
                              'host_port': host_port})

        return ports

    def create_network(self, network, **kwargs):
        current_networks = self.client.networks(names=[network])
        if current_networks:
            return current_networks[0]
        log.debug("Creating docker network '%s'" % network)
        ntwrk = self.client.create_network(network, **kwargs)
        if ntwrk.get('Warning', None):
            log.debug(ntwrk.get('Warning'))
            # Ideally network shouldn't be create with docker client it is !!
            # remove created duplicate network
            self.remove_network(ntwrk.get("Id"))
        else:
            log.debug(
                "Created network with name %s (id: %s)" % (
                    network, ntwrk.get('Id', 'NOT-FOUND'))
            )
        return ntwrk

    def remove_network(self, network):
        log.debug("Removing docker network %s " % network)
        return self.client.remove_network(network)

    def list_networks(self):
        log.debug("listing available docker networks")
        return self.client.networks()

    def get_stats(self, cid, decode=None, stream=True):
        """

        :param cid: The container to stream statistics for
        :param decode:  (bool) If set to true, stream will be decoded
        into dicts on the fly. False by default.
        :param stream: If set to false, only the current stats
         will be returned instead of a stream. True by default.
        :return:
        """
        container_name = self.get_container_name(cid)
        log.debug("Getting stats for container '%s" % container_name)
        return self.client.stats(cid, decode, stream)

    def copy_to_container(self, container, source, dest):
        tar_stream = BytesIO()
        tar_file = tarfile.TarFile(fileobj=tar_stream, mode='w')
        file_data = open(source, mode='rb').read()
        fil_size = os.stat(source).st_size
        tarinfo = tarfile.TarInfo(name=os.path.basename(source))
        tarinfo.size = fil_size
        tarinfo.mtime = time.time()
        # tarinfo.mode = 0600
        tar_file.addfile(tarinfo, BytesIO(file_data))
        tar_file.close()
        tar_stream.seek(0)
        res = self.client.put_archive(container=container['Id'],
                                      path=dest,
                                      data=tar_stream
                                      )
        return res

    def __getattr__(self, item):
        log.debug("Trying to access docker attribute from docker client ")
        return getattr(self.client, item)


class Docker(object):
    # _docker_machine = None
    _docker_client = None
    _containers = []
    _platform = None

    def __init__(self, **kwargs):
        self._platform = get_host()
        self._host_ip = kwargs.pop("host_ip", get_host_ip())
        self._docker_client = DockerClient(**kwargs)

    def setup_docker(self, image, port_binding, links=None, **kwargs):
        self.client.pull_image(image)
        ctr = self.client.find_container('name', kwargs.get('name', None))
        if not ctr:
            host_config = self.client.create_host_config(
                    port_bindings=port_binding,
                    links=links)
            kwargs['host_config'] = host_config
            ctr = self.client.create_container(image, **kwargs)
        self._containers.append(ctr)
        return ctr

    def start_docker(self, ctr, wait_for, clean_up=True, **kwargs):
        self.client.start_container(ctr, wait_for, clean_up,
                                            **kwargs)

    def stop_docker(self, remove=False, **kwargs):
        for ctr in self._containers:
            self.client.stop_container(ctr, remove)

    def cleanup_docker(self):
        self.client.stop_container(self._container_name)
        self.machine.stop()

    @property
    def client(self):
        return self._docker_client

    @property
    def machine_ip(self):
        return self._host_ip

    def port(self, container, priv_port=None):
        return self.client.port(container, priv_port)

    def ip(self, container):
        return self.client.get_container_info(container, "IPAddress")

    def get_container(self, by,  key, all=False):
        return self.client.find_container(by, key, all)

    def get_container_info(self, container, info):
        return self.client.get_container_info(container, info)

