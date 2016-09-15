"""
@author: dhoomakethu
"""

from __future__ import absolute_import, unicode_literals

from apocalypse.utils.vaurien_utils import (VaurienConfigFileParser
                                       as ConfigFileParser)
from apocalypse.utils.vaurien_utils import settings_dict

__all__ = ["ConfigFileParser", "DEFAULT_SETTINGS"]
_marker = []

DEFAULT_VALS = {
    # Generic settings
    "chaos.enabled ": True,
    "chaos.background_run": False,
    "chaos.cloud": "minicloud",
    "chaos.machine": "dev",
    "chaos.error_threshold": 10,
    "chaos.trigger_every": 10,

    # Actions
    # Resource

    # Burn Cpu
    "actions.burn_cpu.enabled": True,
    "burn_cpu.load": 0.9,
    "burn_cpu.load_duration": 30,
    "burn_cpu.vm_instances": None,

    # Burn IO
    "actions.burn_io.enabled": False,

    # Burn RAM
    "actions.burn_ram.enabled": False,
    "burn_ram.load": 0.9,
    "burn_ram.load_duration": 30,
    "burn_ram.vm_instances": None,

    # Burn Disk
    "actions.burn_disk.enabled": False,

    # Generic

    # Kill process
    "actions.kill_process.enabled": True,
    "kill_process.id": None,
    "kill_process.signal": None,
    "kill_process.vm_instances": None,

    "actions.shutdown.enabled": True,
    "actions.reboot.enabled": True,
    "actions.terminate.enabled": False,

    # Network
    "actions.network_blackout.enabled": False,
    "actions.network_error.enabled": False,
    "actions.network_delay.enabled": False,
    "actions.network_hang.enabled": False,
    "actions.network_transient.enabled": False,
    "actions.network_abort.enabled": False,


}
DEFAULT_SETTINGS = settings_dict(DEFAULT_VALS)
