"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
import logging
import os

USE_COLORED_LOGS = True
try:
    import coloredlogs
except ImportError:
    USE_COLORED_LOGS = False


_LOGGERS = {}
CONFIGURED = False
logging.getLogger("requests").propagate = False

FIELD_STYLES = dict(
            asctime=dict(color='green'),
            hostname=dict(color='magenta'),
            levelname=dict(color='blue', bold=False),
            programname=dict(color='cyan'),
            name=dict(color='blue'),
            module=dict(color='cyan'),
            lineno=dict(color='magenta')
    )

LEVEL_STYLES = {
            'DEBUG':    {"color": "blue"},
            'INFO':     {"color": "green"},
            'WARNING':  {"color": "yellow"},
            'ERROR':    {"color": "red"},
            'CRITICAL': {"color": 'red'}
        }

LEVEL_FORMATS = {
        # "INFO": {'fmt': "%(asctime)s - %(levelname)s - "
        #                 "%(module)s - %(message)s"},
        "INFO": {'fmt': "%(levelname)s - %(message)s"},
        "DEBUG": {'fmt': "%(asctime)s - %(levelname)s - "
                         "%(module)s::%(funcName)s @ %(lineno)d - %(message)s"
                  },
        "WARNING": {'fmt': "%(message)s"}
    }


def init_logger(
        name=None,
        log_level='DEBUG',
        no_log=False,
        file_log=False,
        console_log=True,
        log_file=None
):
    global CONFIGURED
    logger = get_logger(__file__)
    if not CONFIGURED:
        configure_logger(
                logger,
                log_level=log_level,
                no_log=no_log,
                file_log=file_log,
                console_log=console_log,
                log_file=log_file
        )
        CONFIGURED = True
    return logger


def get_logger(name=None):
    global _LOGGERS
    name = __file__ if not name else name

    if name not in _LOGGERS.keys():
        _LOGGERS[name] = logging.getLogger(name)

    return _LOGGERS[name]


def configure_logger(
        logger=None,
        log_level='DEBUG',
        no_log=False,
        file_log=False,
        console_log=True,
        log_file=None):

    if not logger:
        logger = get_logger()

    if no_log:
        logger.setLevel(logging.ERROR)
        logger.addHandler(logging.NullHandler())
    else:
        logger.setLevel(log_level.upper())
        fmt = (
            "%(asctime)s - %(message)s"
        )
        fmtr = formatter()
        if console_log:
            if USE_COLORED_LOGS:
                coloredlogs.install(level=os.environ.get('COLOREDLOGS_LOG_LEVEL', log_level.upper()),
                                    fmt=fmt,
                                    field_styles=FIELD_STYLES,
                                    level_styles=LEVEL_STYLES,
                                    overridefmt=LEVEL_FORMATS)
            else:
                sh = logging.StreamHandler()
                sh.setFormatter(fmtr)
                sh.setLevel(log_level.upper())
                logger.addHandler(sh)

        if file_log:
            if log_file is not None:
                func_log = os.path.abspath(log_file)
                os.mkdir(os.path.dirname(func_log))
                fh = logging.FileHandler(func_log)
                fh.setFormatter(fmtr)
                fh.setLevel(log_level)
                logger.addHandler(fh)


class formatter(logging.Formatter):
    info_fmt = logging.Formatter(LEVEL_FORMATS['INFO']['fmt'])
    debug_fmt = logging.Formatter(LEVEL_FORMATS['DEBUG']['fmt'])
    warning_fmt = logging.Formatter(LEVEL_FORMATS['WARNING']['fmt'])

    def format(self, record):

        if record.levelno == logging.DEBUG:
            return self.debug_fmt.format(record)
        elif record.levelno == logging.WARNING:
            return self.warning_fmt.format(record)
        else:
            return self.info_fmt.format(record)