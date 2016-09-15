# """
# @author: dhoomakethu
# """
from __future__ import absolute_import, unicode_literals

from apocalypse.utils.logger import get_logger
import types
import random

chaos_logger = get_logger()


def register(executor_klass):
    """
    Registers a chaos event class with ChaosExecutor class
    Args:
        executor_klass:

    Returns:

    """
    def _register(chaos_klass):
        if chaos_klass.enabled:
            name = chaos_klass.__name__
            if isinstance(chaos_klass, (type, types.ClassType)):
                chaos_klass = chaos_klass()
            setattr(executor_klass, name, chaos_klass)
            # event_klass._chaos_events.update([(name.upper(), chaos_klass)])
            executor_klass.update_events([(name.upper(), chaos_klass)])
            return chaos_klass
    return _register



class SSH(object):
    """
    SSH action
    """
    def __init__(self, host, user, priv_key=None):
        self._host = host
        self._user = user
        self._key = priv_key is not None and "-i %s" % priv_key or ""

    def command(self, cmd):
        return ("ssh %s -l %s %s %s" %
                (self._key, self._user, self._host, cmd)).replace("  ", " ")


class ExecutorBase(type):
    """
    Metaclass for Chaos Executor class
    Updates all the registered chaos events
    """
    def __init__(cls, name, bases, dct):
        super(ExecutorBase, cls).__init__(name, bases, dct)
        # for k, v in dct.items():
        #     if k != 'ACTIONS' and isinstance(v, (types.FunctionType,
        #                                          staticmethod)):
        #         if not k in dct['EXCLUDE']:
        #             dct["ACTIONS"][k.upper()] = v

    def __new__(meta, name, bases, attrs, **kwargs):
        return super(ExecutorBase, meta).__new__(meta, name, bases,
                                                 attrs, **kwargs)

    def __call__(cls, *args, **kwargs):
        return type.__call__(cls, *args, **kwargs)


class ChaosEventBase(type):

    def __new__(meta, name, bases, attrs, **kwargs):
        options = {'services': [
            "micro services to run '%s' chaos against",
            list,
            []]
        }

        if attrs.get('options', None):
            attrs['options'].update(options)
        else:
            attrs['options'] = options
        return super(ChaosEventBase, meta).__new__(meta, name, bases,
                                                   attrs, **kwargs)


class ChaosEvent(object):
    """
    Base Chaos events class

    Command line options are provided for each event is to be extended from
    class dict 'options' with in the derived class

    Each key, value pair in the options dict needs to be in the format of
    option-name, option, where option is a tuple of
    (description, type_, default, choices) choices being optional

    E.g
    class ChaoseventA(Chaos):
        options = {'instance': ("virtual machine instance to run %s chaos
         against", list, [])
        }

    the cli option on py.chaos --help for this option will be displayed as
    --chaoseventa.instance

    """
    __metaclass__ = ChaosEventBase
    _category = "generic"
    enabled = True

    def __init__(self, driver=None):
        # update default option
        self.options['services'][0] %= self.__class__.__name__
        self.app = driver

    def _prepare(self, event):
        vm = self.app.choice(services=self.services, event=event)
        if vm:
            chaos_logger.info("Executing chaos event "
                              "'%s' on '%s" % (self.__class__.__name__, vm))
        return vm

    @property
    def category(self):
        return self._category
