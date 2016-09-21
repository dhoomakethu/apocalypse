"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
import os
import pprint
from apocalypse.chaos.generator import ChaosGenerator
from apocalypse.app.chaosapp import ChaosApp
from apocalypse.utils.deamonize import startstop
from apocalypse.utils.logger import init_logger
from apocalypse.utils.helpers import banner
from apocalypse.exceptions import NoServiceRunningError, NetError
import signal

LOGFILE = '/tmp/twister.log'
PIDFILE = '/tmp/twister.pid'


def handle_sigterm(signal, frame):
    print "SIGTERM event called"
    SystemExit


signal.signal(signal.SIGTERM, handle_sigterm)


def _make_port_map(_iterable):
    it = [x for y in _iterable for x in y.split(":")]
    it = iter(it)
    return {x: y for x, y in zip(it, it)}


def filter_event_args(args):
    events = {event.lower(): {} for event in args.events}
    for _arg in [attr for attr in dir(args)
                 if not callable(attr) and not attr.startswith("__")]:

        # _arg = burncpu_cores
        temp = _arg.split("_", 1)  # temp = [burncpu, cores]
        if len(temp) == 2:
            action, option = temp
            if action in events.keys() and action != _arg:
                events[action].update({option: getattr(args, _arg)})

    return events


def main(args):
    # Initialize
    log_level = args.log_level

    log_file = args.file_log
    logger = init_logger(log_level=log_level,
                         file_log=True if log_file is not None else False,
                         console_log=not args.no_console_log)
    if args.subparser == "server":
        logger.warning(banner("=") + "\n")
        logger.info("Starting Chaos webserver on %s:%s , minicloud network "
                    "%s \n" % (args.host, args.port, args.network))
        logger.warning(banner("=") + "\n")
        # Set environment variables for network
        os.environ["NETWORK"] = args.network
        from apocalypse.server.app import web_app

        debug = True if log_level == "debug" else False
        web_app.run(args.host, args.port, debug=debug)
    else:
        error_threshold = args.error_threshold if args.error_threshold > 0 else 1
        trigger_every = getattr(args, 'trigger', 10)
        try:
            float(trigger_every)
            trigger_unit = "s"
        except ValueError:
            trigger_unit = ""
        filter_categories = {
            "resource": args.run_resource_chaos,
            "generic": args.run_generic_chaos,
            "network": args.run_network_chaos
        }
        max_workers = getattr(args, 'max_workers', 10)
        ChaosGenerator.set_threshold(error_threshold)
        network = args.network
        try:
            error = False
            app = ChaosApp(network)
        except NoServiceRunningError:
            logger.critical(
                "No active containers/services "
                "found for network : \033[1m '%s' \033[0m" % network)

            error = True
        except NetError:
            logger.critical(
                "Network not found : \033[1m '%s' \033[0m" % network)

            error = True
        finally:
            if error:
                logger.critical("Stopping Apocalypse!!!")
                exit(1)
        events = filter_event_args(args)
        if events:
            network_chaos_enabled = args.enable_network_chaos
            extra = {'network_chaos': network_chaos_enabled}
            if network_chaos_enabled:
                app.init_network_emulator()

        gen = ChaosGenerator(app, every=trigger_every,
                             max_workers=max_workers, **extra)
        categorized_events = [e for k, v in filter_categories.items()
                              if v for e in
                              gen._chaos_executor.get_events_by_category(k)]
        if categorized_events:
            events = {k: v for k, v in events.items()
                      if k.lower() in categorized_events}
        background_run = args.background_run

        start = args.start
        stop = args.stop
        status = args.status

        if start:
            logger.warning(banner("info"))
            config = getattr(args, "config", None)
            if config:
                logger.warning("Chaos configuration read from '%s'" % config)
            logger.warning(
                "Starting Chaos with events on network: '%s'" % network)
            logger.warning(banner("="))

            logger.warning(pprint.pformat(events))
            logger.warning(banner("="))
            logger.warning("Chaos would be triggered "
                           "every %s%s" % (trigger_every, trigger_unit))
            logger.warning("Error Threshold set to %s" % error_threshold)

            gen.update_events(events)
            if background_run:
                logger.warning("Logfile @ %s " % LOGFILE)
                logger.warning(banner("=", pad=False)

                               )
                startstop(stdout=LOGFILE, pidfile=PIDFILE,
                          action="start")
            else:
                pid = os.getpid()
                logger.warning("use 'kill %s' to stop chaos\n" % pid)
                logger.warning(banner("=", pad=False))
            gen.start()
        elif stop:
            startstop(stdout=LOGFILE, pidfile=PIDFILE,
                      action="stop")
        elif status:
            startstop(stdout=LOGFILE, pidfile=PIDFILE,
                      action="status")
        else:
            logger.error("Chaos action not specified use one from [start,stop,"
                         "status]")

