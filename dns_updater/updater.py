# -*- coding: utf-8 -*-

import fcntl
import importlib
import os
import signal
import sys
import time

from oslo_config import cfg

from dns_updater.config import setup_config
from dns_updater.utils.tool_classes import (QApplication)
from dnsdb_common.library.exception import UpdaterErr
from dnsdb_common.library.log import (getLogger, setup)

setup('dnsdb_upater_zone')
log = getLogger(__name__)

fp = None
CONF = cfg.CONF


def _get_handler():
    mapping = {
        'ViewMaster': 'dns_updater.workers.view_worker',
        'default': 'dns_updater.workers.zone_worker'
    }
    zone_group = CONF.host_group
    if not zone_group.endswith('Master'):
        raise UpdaterErr('%s, slave group does not need to start updater.' % zone_group)
    # dnsdb请求zone信息
    module = importlib.import_module(mapping.get(zone_group, mapping['default']))
    return module.handler


def _create_pid_file():
    global fp
    pidfile = CONF.etc.pidfile
    if pidfile is None:
        raise UpdaterErr("No pidfile option found in config file.")
    try:
        fp = open(pidfile, 'w')
        # LOCK_EX    /* exclusive lock */
        # LOCK_NB   * don't block when locking */
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp.truncate()
        pid = os.getpid()
        fp.write(str(pid))
        fp.flush()
    except Exception as e:
        raise UpdaterErr("Failed to lock pidfile, perhaps named_updater is already running.")


def _check_necessary_options():
    needed_conf_options = {
        'etc': ["log_dir", "tmp_dir", "backup_dir", "pidfile", 'env'],
        'MAIL': ['from_addr', 'server', 'port', 'info_list', 'alert_list'],
    }

    for section, options in needed_conf_options.items():
        if not hasattr(CONF, section):
            raise UpdaterErr(message=section + " section not found.")

        sec = getattr(CONF, section)
        for op in options:
            if not hasattr(sec, op):
                raise UpdaterErr(message="%s.%s option not found." % (section, op))

            if op.endswith('_dir'):
                dir_path = getattr(CONF.etc, op)
                if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                    raise UpdaterErr(message='No such directory: %s' % dir_path)


def _signal_handler(n=0, e=0):
    log.error("Shuting down normally.")
    sys.exit(0)


class DnsdbUpdater(QApplication):
    name = "dnsdb-zone-updater"
    version = "1.0"

    def init_config(self, argv=None):
        setup_config(sys.argv[1], 'dnsdb-updater', conf_dir=os.path.dirname(os.path.dirname(__file__)))
        log.error('Host belong to group: %s' % CONF.host_group)

    def init_app(self):  # 可选
        super(DnsdbUpdater, self).init_app()
        try:
            _check_necessary_options()
            _create_pid_file()
            # SIGTERM  software termination signal
            signal.signal(signal.SIGTERM, _signal_handler)
        except Exception as e:
            log.exception(e, exc_info=1)
            sys.exit(1)

    def main_loop(self):
        handler = _get_handler()
        while True:
            handler()
            time.sleep(CONF.etc.zone_update_interval)


updater = DnsdbUpdater().make_entry_point()

if __name__ == '__main__':
    updater()
