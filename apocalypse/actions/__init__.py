"""
@author: dhoomakethu

"""
from __future__ import absolute_import, unicode_literals
import types


def register(action_klass):
    """
    Registers a chaos action class with Action class
    Args:
        action_klass:

    Returns:

    """
    def _register(chaos_klass):
        if chaos_klass.enabled:
            name = chaos_klass.__name__
            if isinstance(chaos_klass, (type, types.ClassType)):
                chaos_klass = chaos_klass()
            setattr(action_klass, name, chaos_klass)
            action_klass._actions.update([(name.upper(), chaos_klass)])
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


class ActionBase(type):
    """
    Metaclass for Action class
    Updates all the registered chaos actions
    """
    def __init__(cls, name, bases, dct):
        super(ActionBase, cls).__init__(name, bases, dct)
        # for k, v in dct.items():
        #     if k != 'ACTIONS' and isinstance(v, (types.FunctionType,
        #                                          staticmethod)):
        #         if not k in dct['EXCLUDE']:
        #             dct["ACTIONS"][k.upper()] = v

    def __new__(meta, name, bases, attrs, **kwargs):
        return super(ActionBase, meta).__new__(meta, name, bases,
                                               attrs, **kwargs)

    def __call__(cls, *args, **kwargs):
        return type.__call__(cls, *args, **kwargs)
