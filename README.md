# **Apocalypso** #

Apocalypso is resilience test tool to test the behaviour of `Docker Ecosystem` under various failure conditions (Network/hardware/termination etc)

## Pre-requisites ##
* [docker](https://docs.docker.com/engine/installation/)
* [docker-compose](https://docs.docker.com/compose/install/)

## Build ##
```
$ python setup.py sdist
```

## Installation ##
```
$ easy_install dist/apocalypse-<version>.tar.gz
```
or
```
$ pip install git+https://github.com/dhoomakethu/apocalypso.git@master
```
For Colored logs install coloredlogs
```
$ pip install git+https://github.com/dhoomakethu/python-coloredlogs.git@master
```

## Usage ##
```
$ doom --help

   _____                              .__                              ._._.
  /  _  \ ______   ____   ____ _____  |  | ___.________  ______ ____   | | |
 /  /_\  \\____ \ /  _ \_/ ___\\__  \ |  |<   |  \____ \/  ____/ __ \  | | |
/    |    |  |_> (  <_> \  \___ / __ \|  |_\___  |  |_> \___ \\  ___/   \|\|
\____|__  |   __/ \____/ \___  (____  |____/ ____|   __/____  >\___  >  ____
        \/|__|               \/     \/     \/    |__|       \/     \/   \/\/


                                                                Chaos Generator for Docker Ecosystems!!
                                                                version: 1.0.0

usage: doom {chaos|events|server} <optional params>

positional arguments:
  {chaos,events,server}
                        help for subcommand chaos
    chaos               Start Chaos generator
    events              Chaos events
    server              Chaos web server

optional arguments:
  -n NETWORK, --network NETWORK
                        docker network (default: None)
  --log-level {info,debug,error,critical}
                        log level (default: None)
  --no-console-log      disable console log (default: False)
  --file-log FILE_LOG   path for log file (default: None)
  --background-run      Runs chaos in background (default: False)
  -e ERROR_THRESHOLD, --error-threshold ERROR_THRESHOLD
                        Keeps Chaos generator till the error threshold is
                        reached (should be > 0),value < 0 is reset to 1
                        (default: None)
  --config CONFIG       Configuration file (default: None)
  --version             show program's version number and exit

  
```

There are three subparsers defined chaos and actions.

```
$ doom chaos --help

usage: doom chaos <optional params>

optional arguments:
  --start               Start Chaos Generator (default: False)
  --stop                Stop Chaos Generator (default: False)
  --status              status of chaos generator (default: False)
  -e EVENTS [EVENTS ...], --events EVENTS [EVENTS ...]
                        Chaos events to execute (default: [])
  -t TRIGGER, --trigger TRIGGER
                        Trigger chaos for every given time (in
                        Sec/Minute/Hour) (default: None)
  --max-workers MAX_WORKERS
                        Max worker threads to spawn (default: None)
  --enable-network-chaos
                        enables network chaos (default: False)
  --run-network-chaos   Runs only network chaos (default: False)
  --run-resource-chaos  Runs only resource chaos (burn cpu/ram/kill process
                        etc) (default: False)
  --run-generic-chaos   Runs only generic chaos (stop/reboot/terminate
                        containers (default: False)
  --version             show program's version number and exit


```

```
$ doom events --help

usage: doom events <optional params>

optional arguments:
  --list-events  List available chaos events supported (default: False)
  --all          display all defined chaos events (default: False)
  --version      show program's version number and exit
```

```
$ doom server --help
usage: doom server <optional params>

optional arguments:
  --host HOST  HOST IP to run the chaos web server on (default: localhost)
  --port PORT  PORT to run the chaos web server on (default: 5555)
  --version    show program's version number and exit
```
##NOTE: All below examples assumes the docker eco system under test is up and running and has a valid docker network associated with

##To Start Chaos Webserver ##
```
$ doom server --port <PORT to START>

```
If no arguments are passed , by default the server will start on **localhost:5555** with default docker network as **apocalypso_default**
##To Start Chaos on network abc##
```
$ doom chaos --start --network abc --events stop kill burncpu

===================================== info =====================================

Starting Chaos on abc with actions
====================================== = =======================================

{'burncpu': {u'cpu_core': 0,
             u'cpuload': 0.5,
             u'duration': 10,
             u'instance': []},
 'kill': {u'instance': [], u'process': None, u'signal': 9},
 'stop': {u'instance': []}}
====================================== = =======================================

Chaos would be triggered every 10 sec
Error Threshold set to 10
use 'kill 71227' to stop chaos

================================================================================

2016-02-24 21:52:13,480 - INFO - generator - Staring Chaos!!!!
================================================================================

```

##To Start Chaos on docker ecosystem from a config file##
This will override all command line options, a sample config file is available at 
[resource chaos](apocalypso/config/chaos.yml) and [network chaos](apocalypso/config/network_chaos.yml) 

```
$ doom chaos --start --config <path to config>
```

##To Start Chaos on docker ecosystem and exit on error threshold##
```
$ doom -e 1 chaos --start --network minicloud_default --actions stop kill burncpu
```

##To Start Chaos on docker ecosystem as deamon process##
```
$ doom --background-run chaos start --network minicloud_default --actions stop kill burncpu
```

##To Stop Chaos running against docker ecosystem##
```
$ kill <pid>
```

##To Stop Chaos running as deamon on docker ecosystem##
```
$ doom chaos --stop --cloud minicloud
```

##To view all the supported chaos events##
```
$ doom events --list-events
```

# **TBD** #
* schedule and mail notifications