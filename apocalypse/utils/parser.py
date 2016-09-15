"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
from apocalypse.exceptions import ConfigParserException
import sys
import argparse
import json
import toml
import yaml
import os

# ------------------------------------------------------------
# Classes
#


class TomlConfigParser(object):

    def read(self, config_file):
        config = {}
        with open(config_file) as conffile:
            config = toml.loads(conffile.read())
        return config

    def write(self, content, config_file):
        with open(config_file, "w+") as conffile:
            conffile.write(toml.dumps(content))


class JsonConfigParser(object):

    def read(self, config_file):
        config = {}
        with open(config_file) as conffile:
            config = json.loads(conffile.read())
        return config

    def write(self, content, config_file):
        with open(config_file, "w+") as conffile:
            conffile.write(json.dumps(content))


class YamlConfigParser(object):

    def read(self, config_file):
        config = {}
        with open(config_file) as conffile:
            config = yaml.load(conffile.read())
        return config

    def write(self, content, config_file):
        with open(config_file, "w+") as conffile:
            yaml.dump(content, conffile, default_flow_style=False)


class ConfigParser(object):
    parsers = {".json": JsonConfigParser,
               ".toml": TomlConfigParser,
               ".yml": YamlConfigParser,
               ".yaml": YamlConfigParser
               }

    @classmethod
    def read(cls, config_file):
        parser = cls.parsers.get(cls.get_file_extension(config_file),
                                 "unknown")
        if parser == "unknown":
            with open(config_file) as conffile:
                config = conffile.read()
        else:
            config = parser().read(config_file)
        return config

    @classmethod
    def write(cls, content, config_file):
        parser = cls.parsers.get(cls.get_file_extension(config_file),
                                 "unknown")
        if parser == "unknown":
            with open(config_file, "w+") as conffile:
                conffile.write(content)
        else:
            parser().write(content, config_file)

    @staticmethod
    def get_file_extension(config_file):
        return os.path.splitext(config_file)[1]


def build_args(parser, items):
    for name, klass in items.items():
        for option_name, option in klass.options.items():
            if len(option) == 3:
                description, type_, default = option
                choices = None
            else:
                description, type_, default, choices = option

            option_name = '--%s-%s' % (name.lower(),
                                          option_name.replace('_', '-'))
            if type_ is bool:
                kws = {'action': 'store_true'}
            elif type_ is list:
                kws = {'nargs': '*'}
            else:
                kws = {'action': 'store', 'type': type_}

            if choices is not None:
                kws = {'choices': choices}

            parser.add_argument(option_name, default=default,
                                help=description, **kws)


class CLIArgParser(argparse.ArgumentParser):
    def __init__(self,
                 title=None,
                 *args,
                 **kwargs):
        """

        Args:
            title: Title of the app

        """

        self.title = title
        kwargs["formatter_class"] = kwargs.get(
            'formatter_class',
            argparse.ArgumentDefaultsHelpFormatter
            # SortedHelpFormatter
        )
        kwargs["add_help"] = False
        super(CLIArgParser, self).__init__(*args,  **kwargs)

    def _fix_parsers(self):
        args = sys.argv[1:]
        optional_actions = []
        subparsers = []
        _subparsers = {}
        for action in self._get_optional_actions():
            optional_actions.extend(action.option_strings)

        for subparser in self._get_positional_actions():
            for choice, _parser in subparser.choices.items():
                subparsers.append(choice)
                _subparsers[choice] = _parser
        # only optional flags / help e.g prog --opt / prog --help
        if subparsers:
            if not len(args):
                #  only prog name
                args.extend(["--help", subparsers[0]])

            elif len(args) == 1 and args[0] in ["--help", "-h"]:
                #  --help/ -h / --version
                args.append(subparsers[0])
            else:  # len(args) > 1
                optional_args = list(set(args) & set(optional_actions))
                if args[0] in subparsers and optional_args:
                    #  optional arguments after parser arguments
                    if "--version" in optional_args:
                        pass
                    else:
                        temp_args = []
                        for _arg in optional_args:
                            temp_args.append(_arg)
                            detail = self._get_option_tuples(_arg)
                            if not detail[0][0].const:  #  store_true
                                temp_args.append(args[args.index(_arg) + 1])
                                args.remove(temp_args[-1])
                            args.remove(_arg)
                        temp_args.extend(args)
                        args = temp_args
            sys.argv[1:] = args
            return _subparsers, args

    def parse(self, args=None, namespace=None):
        """
        Parse known and unknown arguments. This behaves similar to
        ArgumentParser.parse_known_args().

        Returns:
            (Namespace, list):
                Namespace: Instance of known arguments represented as a
                    namespace.
                list: List of unknown arguments.
        """
        orginal_args = sys.argv[1:]
        subparsers, args = self._fix_parsers()
        subparser = list(set(subparsers.keys()) & set(args))
        known, unknown = self.parse_known_args(args, namespace)

        if "-h" in unknown or "--help" in unknown:
            if len(orginal_args) == 1 and ("-h" in unknown or "--help" in unknown):
                self.print_message(self.title+"\n")
                self.print_help()
                exit(0)
            elif len(subparser) == 1:
                subparsers[subparser[0]].print_help()
                exit(0)
        if unknown:
            msg = 'unrecognized arguments: %s'
            self.error(msg % ' '.join(unknown))

        return known

    def print_message(self, message, _file=None):
        if not _file:
            _file = sys.stdout
        if message:
            self._print_message(message, _file)


def configure_cli_parser(name, parser, version=None):
    if version:
        version = '%(prog)s v{version}'.format(version=version)
    else:
        version = '%(prog)s'

    if name == "global":
        return _configure_global_parser_args(parser, version)
    elif name == "chaos":
        return _configure_chaos_parser_args(parser, version)
    elif name == "events":
        return _configure_events_parser_args(parser, version)
    elif name == "server":
        return _configure_server_parser_args(parser, version)
    else:
        raise ConfigParserException("Parser %s not recognised " % name)


def _configure_global_parser_args(parser, version):

    parser.add_argument('-n', '--network',
                       help='docker network', default="bridge")
    parser.add_argument('--log-level',
                        help='log level',
                        choices=['info', 'debug', 'error', 'critical'],
                        )
    parser.add_argument('--no-console-log', help='disable console log',
                        action='store_true')
    parser.add_argument('--file-log', help='path for log file',
                        )
    parser.add_argument('--background-run',
                        help='Runs chaos in background',
                        action="store_true")
    parser.add_argument('--events', nargs='+',
                        help='Chaos events to execute',
                        default=[]
                        )
    parser.add_argument('-e', '--error-threshold',
                        help='Keeps Chaos generator till the '
                             'error threshold is reached (should be > 0),'
                             'value < 0 is reset to 1',
                        type=int,
                        )
    parser.add_argument('--config', help='Configuration file', default=None)
    parser.add_argument('--version', action='version', version=version)

    return parser


def _configure_chaos_parser_args(chaos_parser, version):
    chaos_triggers = chaos_parser.add_mutually_exclusive_group()
    chaos_triggers.add_argument("--start", help="Start Chaos Generator",
                                action="store_true")
    chaos_triggers.add_argument("--stop", help="Stop Chaos Generator",
                                action="store_true")
    chaos_triggers.add_argument('--status', help="status of chaos generator",
                                action='store_true')

    chaos_parser.add_argument('-t', '--trigger',
                              help='Trigger chaos for every '
                                   'given time (in Sec/Minute/Hour)',
                              type=str,
                              )
    chaos_parser.add_argument('--max-workers',
                              help='Max worker threads to spawn',
                              type=int,
                              # default=10
                              )
    chaos_parser.add_argument('--enable-network-chaos',
                              help="enables network chaos",
                              action='store_true')

    chaos_parser.add_argument('--run-network-chaos',
                              help="Runs only network chaos",
                              action='store_true')
    chaos_parser.add_argument('--run-resource-chaos',
                              help="Runs only resource chaos (burn "
                                   "cpu/ram/kill process etc)",
                              action='store_true')
    chaos_parser.add_argument('--run-generic-chaos',
                              help="Runs only generic chaos ("
                                   "stop/reboot/terminate containers",
                              action='store_true')

    chaos_parser.add_argument('--version', action='version', version=version)
    return chaos_parser


def _configure_events_parser_args(events_parser, version):
    events_parser.add_argument("--list-events",
                               help="List available chaos events supported",
                               action="store_true")
    events_parser.add_argument('--all', action='store_true',
                               help="display all defined chaos events")
    events_parser.add_argument('--version', action='version', version=version)

    return events_parser


def _configure_server_parser_args(server_parser, version):
    server_parser.add_argument("--host",
                               help="HOST IP to run the chaos web server on",
                               default="0.0.0.0")
    server_parser.add_argument('--port',
                               type=int,
                               help="PORT to run the chaos web server on",
                               default=5555)
    server_parser.add_argument('--version', action='version',
                               version=version)

    return server_parser

#
# class YamlConfigParser(object):
#
#     @staticmethod
#     def read(config_file):
#         config = dict()
#         with open(config_file) as conffile:
#             config = yaml.load(conffile.read())
#         return config
#
#     @staticmethod
#     def write(content, config_file):
#         with open(config_file, "w+") as conffile:
#             yaml.dump(content, conffile, default_flow_style=False)
