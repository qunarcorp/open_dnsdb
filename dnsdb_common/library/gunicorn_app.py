# -*- coding: utf-8 -*-

import multiprocessing

from gunicorn import glogging
from gunicorn.app import base
from gunicorn.six import iteritems


class GunicornLogger(glogging.Logger):
    def access(self, resp, req, environ, request_time):
        # ignore healthcheck
        if environ.get('RAW_URI') == '/healthcheck.html':
            return
        super(GunicornLogger, self).access(resp, req, environ, request_time)


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class GunicornApplication(base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(GunicornApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        config['logger_class'] = GunicornLogger
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
