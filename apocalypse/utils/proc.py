"""
@author: dhoomakethu
"""
from __future__ import absolute_import, unicode_literals
import time
import threading
from Queue import Queue, Empty
import subprocess
from psutil import Process, pid_exists
import atexit
from concurrent.futures import ThreadPoolExecutor

from apocalypse.utils.logger import get_logger

TIMEOUT = 15  # default timeout


class UnexpectedEndOfStream(Exception):
    pass


class MessageNotFound(Exception):
    pass


class TPExecutor(ThreadPoolExecutor):

    # http://stackoverflow.com/a/24457608/2772269

    def make_deamon(self):
        pass

    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super(TPExecutor, self).submit(
            self._function_wrapper, fn, *args, **kwargs)

    def _function_wrapper(self, fn, *args, **kwargs):
        """Wraps `fn` in order to preserve the traceback of any kind of
        raised exception

        """
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            raise e
            # raise sys.exc_info()[0](traceback.format_exc())  # Creates an
                                                             # exception of the
                                                             # same type with the
                                                             # traceback as
                                                             # message

log = get_logger()


class Proc(object):
    _q = Queue()
    _out_stream = None
    _error_stream = None

    def __init__(self, cmd, shell=False, stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 cleanup=True,
                 **kwargs
                 ):
        self._proc = None
        self._cmd = cmd
        self._shell = shell
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._kwargs = kwargs
        self._pid = None
        self.running = False
        if cleanup:
            atexit.register(self.kill)

    def run(self, wait_for=None, timeout=None, blocking=False):
        self._proc = subprocess.Popen(self._cmd, shell=self._shell,
                                      stdout=self._stdout, stdin=self._stdin,
                                      stderr=self._stderr, **self._kwargs)
        self._pid = self._proc.pid
        self.running = True

        found = threading.Event()
        self._out_stream = NonBlockingStreamReader(self._proc.stdout,
                                                   look_for=wait_for,
                                                   found=found)
        self._error_stream = NonBlockingStreamReader(self._proc.stderr,
                                                     look_for=wait_for,
                                                     found=found)

        if wait_for is not None:
            timeout = timeout if timeout is not None else TIMEOUT
            status = found.wait(timeout)
            if not status:
                out, error = self.proc_output()
                out.extend(error)
                error = "\n".join(out)
                log.error("Expected string not found in output")
                log.error("captured log from the application")
                log.error("-----------------------------------")
                log.error(error)
                log.error("-----------------------------------")
                raise MessageNotFound('not found: %s' % wait_for)
        elif blocking:
            status = self._proc.poll()
            while status is None:
                time.sleep(0.5)
                status = self._proc.poll()
        else:
            if timeout is not None:
                while timeout > 0:
                    if self._proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    timeout -= 0.1

    @property
    def proc(self):
        return self._proc

    def kill(self, pid=None):
        if self.running:
            pid = self._pid if pid is None else pid
            if pid_exists(pid):
                log.debug("killing process with pid %s" % pid)

                process = Process(pid)
                self._out_stream.stop()
                self._error_stream.stop()
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()

    def proc_output(self):
        return self._get_stdout(), self._get_stderr()

    def _get_stdout(self):
        out = []
        if self._out_stream is not None:
            while True:
                line = self._out_stream.readline(0.1)
                if not line:
                    break
                out.append(line.strip())
        return out

    def _get_stderr(self):
        err = []
        if self._error_stream is not None:
            while True:
                line = self._error_stream.readline(0.1)
                if not line:
                    break
                err.append(line.strip())
        return err

    def __enter__(self):
        log.debug("entering proc context manager")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug("exiting proc context manager")
        self.kill()
        # Handle any exceptions outside
        return False


class NonBlockingStreamReader:

    def __init__(self, stream, look_for=None, found=threading.Event()):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()
        self._running = threading.Event()
        self._running.set()

        def _enqueu_queue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while self._running.is_set():
                line = stream.readline()
                if line:
                    log.info(line)
                    queue.put(line)
                    if look_for is not None:
                        if look_for in line:
                            found.set()
                            break
                else:
                    break

        self._t = threading.Thread(target=_enqueu_queue,
                                   args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None

    def stop(self):
        self._running.clear()


if __name__ == "__main__":
    import os
    from apocalypse.utils.logger import init_logger
    init_logger("test")
    os.environ["PATH"] += os.pathsep + "/usr/local/bin"
    cmd = ["docker-machine", "ls"]
    with Proc(cmd) as p:
        p.run("dev")
        # p.run("dev2", timeout=3)
