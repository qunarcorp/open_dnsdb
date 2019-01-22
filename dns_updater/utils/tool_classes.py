# -*- coding: utf-8 -*-

import sys
import threading
from Queue import Queue

from oslo.config import cfg

from dnsdb_common.library.log import getLogger, setup
from dnsdb_common.library.exception import UpdaterErr
from dnsdb_common.library.singleton import Singleton
log = getLogger(__name__)

setup('QApplication')
CONF = cfg.CONF


def parse_args(argv, version, default_config_files=None):
    cfg.CONF(argv[1:],
             project='qlib',
             version=version,
             default_config_files=default_config_files)


class QApplication(Singleton):
    name = "QApplication"
    version = "0"

    def init_config(self, argv=None):
        is_argv_specified = False
        if isinstance(argv, (list, tuple)):
            is_argv_specified = True
            argv = [sys.argv[0]] + list(argv)
        if not is_argv_specified:
            argv = sys.argv
        parse_args(argv, self.version)

    def setup_logger(self):
        setup(self.name)

    def init_app(self):
        pass

    def on_shutdown(self):
        pass

    def main_loop(self):
        raise UpdaterErr('This function has not been implemented yet')

    def run(self):
        log.debug("app: %s, version: %s",
                  self.name, self.version)
        log.debug("Initializing the application.")
        self.init_config()
        self.setup_logger()
        self.init_app()
        log.debug("Starting the application.")
        self.main_loop()
        self.on_shutdown()
        log.debug("Shutdown the application.")

    def make_entry_point(self):
        def wrap():
            self.run()

        return wrap


class GenericWorker(threading.Thread):
    def __init__(self, interval):
        self.interval = interval
        self.event = threading.Event()
        self._is_running = False
        super(GenericWorker, self).__init__()

    def handler(self):
        raise NotImplementedError

    def run(self):
        log.info('%s thread start.' % self.__class__.__name__)
        self._is_running = True
        while self._is_running:
            self.handler()
            if self.event.wait(self.interval):
                break


    def stop(self):
        log.info('%s thread stop.' % self.__class__.__name__)
        self._is_running = False
        self.event.set()


class ZoneUpdateHandler(threading.Thread):
    def __init__(self, queue, handler):
        super(ZoneUpdateHandler, self).__init__()
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.zones_to_update = set()
        self.zones_queues = Queue()
        self.queue_name = queue
        self.daemon = True
        self.handler = handler

    def run(self):
        log.info('ZoneUpdateHandler thread start.')
        while not self.event.wait(0.1):
            zone = self.zones_queues.get()
            with self.lock:
                self.zones_to_update.remove(zone)
            self.handler(zone)
        log.error('ZoneUpdateHandler thread end.')

    def add_zones(self, zones):
        for zone in zones:
            with self.lock:
                if zone not in self.zones_to_update:
                    self.zones_to_update.add(zone)
                    self.zones_queues.put(zone)
                    if not self.isAlive():
                        log.error('ZoneUpdateHandler thread is stopped by accident.')
                        raise Exception

