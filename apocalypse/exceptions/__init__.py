"""
@author: dhoomakethu

"""
from __future__ import absolute_import, unicode_literals


class TwisterException(Exception):
    """
    Base exception with in Twister
    """


class ConfigParserException(Exception):
    """
    Error in configuration
    """


class UnknownChaosEvent(TwisterException):
    """
    Unknow chaos action execption
    """

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "Unknown action: %s." % self._name

    def __unicode__(self):
        return unicode(self.__str__())


class ServiceNotRunningError(TwisterException):
    """
    No Specified VM exists exception
    """


class InsufficientPermissionsException(TwisterException):
    """
    Twister is executed with insufficient permissions
    """


class AppError(TwisterException):
    """Webserver applocation errors"""
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super(AppError, self).__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class NetError(AppError):
    """Error while executing network events"""


class UnknownServiceError(TwisterException):
    """Service info not available"""
