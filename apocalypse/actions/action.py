"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
from apocalypse.actions import ActionBase
import random
import types
from apocalypse.utils.logger import get_logger
from apocalypse.utils.helpers import banner

action_logger = get_logger()


def actions():
    return Action.list_actions()


def unregister(action):
    Action.unregister(action)


class Action(object):
    """
    Action class responsible for executing chaos actions.
    """

    _actions = {}
    __metaclass__ = ActionBase

    def __init__(self, compute_engine):
        self.ce = compute_engine

    def __new__(cls, *args, **kwargs):
        return super(Action, cls).__new__(cls, *args, **kwargs)

    def __call__(self, action, *args, **kwargs):
        _action = self._actions.get(action)
        if _action:
            action_logger.debug("Calling action %s on %s" % (action, self.ce))
            if isinstance(_action, (types.InstanceType,
                                    types.ObjectType, staticmethod)):
                return _action(self.ce, *args, **kwargs)
            elif isinstance(_action, types.FunctionType):
                return _action(self, *args, **kwargs)
            else:
                raise UnknownAction(action)
        else:
            action_logger.error("Unknown action requested :%s" % action)
            raise UnknownAction(action)

    @classmethod
    def register(cls, action):
        action_logger.info("Registering action :%s" % action)
        if isinstance(action, (types.FunctionType, staticmethod)):
            name = action.__name__
            cls._actions[name.upper()] = action
            setattr(cls, name, action)
        elif isinstance(action, types.ClassType) and hasattr(action, "__call__"):
            name = action.__name__
            action = action()
            cls._actions[name.upper()] = action
            setattr(cls, name, action)
        elif (isinstance(action, (types.InstanceType, types.ObjectType))
              and hasattr(action, "__call__")):
            if isinstance(action, type):
                name = action.__name__
                action = action()
            else:
                name = action.__class__.__name__
            cls._actions[name.upper()] = action
            setattr(cls, name, action)

        else:
            name = str(action)
            action_logger.error("Error registering action :%s" % action)
            raise UnknownAction("unable to register action %s!!" %name)

    @classmethod
    def unregister(cls, action):
        action_logger.info("Un-registering action :%s" % action)
        name = action.upper()
        if cls._actions.get(name):
            # if hasattr(self, action):
            #     delattr(self, action)
            del cls._actions[name]

    def run(self, action, *args, **kwargs):
        action_logger.warning(banner("=", pad=False))
        action_logger.info("Running action :%s" % action)
        return self.execute(action, *args, **kwargs)

    def random_run(self, *args, **kwargs):
        action = random.choice(self._actions.keys())
        action_logger.warning(banner("=", pad=False))
        action_logger.info("Running random action :%s" % action)
        return self.run(action, *args, **kwargs)

    @property
    def actions(self):
        return sorted(self._actions.keys())

    @actions.setter
    def actions(self, value):
        self._actions.update(value)

    @classmethod
    def list_actions(cls):
        return cls._actions

    def execute(self, action, *args, **kwargs):
        action_logger.debug("Executing action %s" % action)
        action = action.upper()
        try:
            res = self(action, *args, **kwargs)
            action_logger.info("Done executing chaos action: %s" % action)
            action_logger.warning(banner("=", pad=False))
            return res
        except AttributeError as e:
            raise UnknownAction(e)

    def is_registered(self, action):
        action_logger.info("Checking action %s is registered" % action)
        return action.upper() in self.list_actions()

    def build_args(self):
        pass


class UnknownAction(Exception):

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "Unknown action: %s." % self._name

    def __unicode__(self):
        return unicode(self.__str__())
