import threading
from apocalypse.utils.logger import get_logger
logger = get_logger()


class BackgroundJob(threading.Thread):
    def __init__(self, name, interval, function, *funcargs, **funckwargs):
        threading.Thread.__init__(self)
        self._name = name
        self.interval = interval
        self.task = function
        self.stop_timer = threading.Event()
        self.funcargs = funcargs
        self.funckwargs = funckwargs

    def run(self):
        logger.debug("Start %s thread" % self._name)
        while not self.stop_timer.is_set():
            if not self.stop_timer.is_set():
                self.task(*self.funcargs, **self.funckwargs)
            self.stop_timer.wait(self.interval)
        logger.debug("Stop %s thread" % self._name)

    def cancel(self):
        self.stop_timer.set()

