"""
@author: dhoomakethu

"""
from __future__ import absolute_import, unicode_literals


class HandleException(object):
    func = None

    def __init__(self, logger, *exceptions):
        self.logger = logger
        self.exceptions = tuple(ex for ex in exceptions
                                if issubclass(ex, Exception)
                                or
                                isinstance(ex, Exception)
                                )
        if not self.exceptions:
            self.exceptions = Exception

    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        # self.func = args[0]
        try:
            return self.func(*args, **kwargs)
        except self.exceptions as e:
            self.logger.debug("IN HandleExceptions")
            self.logger.debug(e)
            raise e
        except Exception as e:
            self.logger.debug("IN Generic Exception handler")
            self.logger.debug(e)
            raise e


def handle_exception(logger, retVal, *exceptions):
    """
    Decorator to handle known exceptions

    :param logger: logger
    :param retVal: "exit" to exit program, "raise" to re-raise execption
    :param exceptions: list of exceptions to handle
    :return: return value of function decorated
    """

    def except_wrapper(func):
        excpts = tuple(ex for ex in exceptions if issubclass(ex, Exception)
                       or isinstance(ex, Exception)
                       )

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except excpts as e:
                logger.debug(e)
                logger.debug("supplied arguments %s: %s" % (args[1:], kwargs))
                if retVal == "raise":
                    raise e
                elif retVal == "exit":
                    logger.critical(e.message)
                    logger.critical("Stopping Apocalypse!!!")
                    exit(1)

        return wrapper

    return except_wrapper


class ApocalypseError(Exception):
    """
    Base exception with in Apocalypse
    """


class ConfigParserException(Exception):
    """
    Error in configuration
    """


class UnknownChaosEvent(ApocalypseError):
    """
    Unknow chaos action execption
    """

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "Unknown action: %s." % self._name

    def __unicode__(self):
        return unicode(self.__str__())


class ServiceNotRunningError(ApocalypseError):
    """
    No Specified VM exists exception
    """


class InsufficientPermissionsException(ApocalypseError):
    """
    Twister is executed with insufficient permissions
    """


class AppError(ApocalypseError):
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


class UnknownServiceError(ApocalypseError):
    """Service info not available"""


class NoServiceRunningError(ApocalypseError):
    """No service found running for the given network"""
