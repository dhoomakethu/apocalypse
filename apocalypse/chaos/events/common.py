"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals

import re

from apocalypse.utils.logger import get_logger

from apocalypse.chaos import register, SSH
from apocalypse.chaos import ChaosEvent
from apocalypse.chaos.executor import ChaosExecutor

pid_regexp = re.compile(r"^\d+$")

chaos_logger = get_logger()

__all__ = ["Terminate", "Stop", "Reboot", "KillProcesses"]


@register(ChaosExecutor)
class Terminate(ChaosEvent):
    enabled = True

    def _terminate(self):
        """
        terminates a vm (stop + rm)
        """
        vm = self._prepare('Terminate')
        return self.app.terminate_services(
            services=vm if isinstance(vm, (list, tuple)) else [vm])

    def __call__(self, driver, services=None):
        self.app = driver
        self.services = services
        return self._terminate()


@register(ChaosExecutor)
class Stop(ChaosEvent):
    enabled = True

    def _stop(self):
        """
        stops a vm
        """
        vm = self._prepare('Stop')
        return self.app.stop_services(
            services=vm if isinstance(vm, (list, tuple)) else [vm])

    def __call__(self, driver, services=None):
        self.app = driver
        self.services = services
        return self._stop()


@register(ChaosExecutor)
class Reboot(ChaosEvent):
    enabled = True

    def _reboot(self):
        """
        reboots a vm
        """
        vm = self._prepare('Reboot')
        return self.app.reboot_services(
            services=vm if isinstance(vm, (list, tuple)) else [vm])

    def __call__(self, driver, services=None):
        self.app = driver
        self.services = services
        return self._reboot()


@register(ChaosExecutor)
class KillProcesses(ChaosEvent):
    enabled = True
    _category = "resource"
    options = {
        'process_id': [
            "pid of the process to be killed",
            int,
            None
        ],
        'signal': [
            'signal to be sent to the process',
            int,
            9
        ],

    }

    def _kill(self):
        vm = self._prepare('KillProcesses')
        return self.app.kill_process(
            services=vm if isinstance(vm, (list, tuple)) else [vm],
            process=self.process,
            signal=self.signal)

    def __call__(self, driver, process_id=None, signal=9, services=None):
        """
        Kills a process, sending the given signal.
        """
        self.app = driver
        self.process = process_id
        self.signal = signal
        self.services = services
        return self._kill()


@register(ChaosExecutor)
class RemoteKill(ChaosEvent):
    enabled = False

    def _remote_kill(self):
        vm = self._prepare('RemoteKill')
        cmd = "{sudo} {cmd} -{signal} {process}"
        cmd = cmd.format(sudo=self._sudo, cmd=self._cmd, signal=self._signal,
                         process=self._process)
        return self.app.remote_kill_process(
            services=vm if isinstance(vm, (list, tuple)) else [vm],
            process=self._process,
            signal=self._signal,
            ssh=self._ssh,
            cmd=cmd,
            sudo=self._sudo
        )

    def __call__(self, driver, process, host, user,
                 signal=9, priv_key=None, use_sudo=True, services=None):
        self.app = driver
        self.services = services
        proc = str(process)
        self._ssh = SSH(host, user, priv_key)
        self._process = proc
        self._cmd = pid_regexp.match(proc) is not None and "kill" or "killall"
        self._signal = signal
        self._sudo = use_sudo and "sudo" or ""

        # os.system(self._ssh.command(cmd))
        return self._remote_kill()


@register(ChaosExecutor)
class UpstartStop(ChaosEvent):
    enabled = False

    def _upstart_stop(self):

        vm = self._prepare('UpstartStop')
        cmd = "sudo stop %s" % self._job
        return self.app.stop_upstart_job(
                services=vm if isinstance(vm, (list, tuple)) else [vm],
                ssh=self._ssh,
                job=self._job,
                cmd=cmd
        )

    def __call__(self, driver, job, host, user, priv_key=None,
                 services=None):
        self.app = driver
        self.services = services
        self._ssh = SSH(host, user, priv_key)
        self._job = job
        return self._upstart_stop()
        # cmd = "sudo stop %s" % self._job
        # os.system(self._ssh.command(cmd))


@register(ChaosExecutor)
class InitdStop(ChaosEvent):
    enabled = False

    def _initd_stop(self):
        vm = self._prepare('InitdStop')
        cmd = "sudo /etc/init.d/{0} stop".format(self._job)
        return self.app.stop_initd_job(
                services=vm if isinstance(vm, (list, tuple)) else [vm],
                ssh=self._ssh,
                job=self._job,
                cmd=cmd
        )

    def __call__(self, driver, host, job, user, priv_key=None,
                 services=None):
        self.app = driver
        self.services = services
        self._ssh = SSH(host, user, priv_key)
        self._job = job
        return self._initd_stop()
