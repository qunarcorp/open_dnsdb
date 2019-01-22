# -*- coding: utf-8 -*-
#
# Copyright 2013, Qunar OPSDEV
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# Author: jaypei <jaypei97159@gmail.com>
#

import multiprocessing
import sys

from flask import Flask
from oslo.config import cfg
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from ..library.exception import DnsdbException
from ..library.singleton import Singleton

CONF = cfg.CONF

CONF.register_cli_opts([
    cfg.StrOpt('base-url',
               default='/',
               help='The url prefix of this site.'),
    cfg.StrOpt('run-mode',
               default="werkzeug",
               choices=('gunicorn', 'werkzeug'),
               help="Run server use the specify mode."),
    cfg.StrOpt('bind',
               default='0.0.0.0',
               help='The IP address to bind'),
    cfg.IntOpt('port',
               default=8080,
               help='The port to listen'),
], 'web')

CONF.register_cli_opts([
    cfg.StrOpt('config',
               default=None,
               help='The path to a Gunicorn config file.'),
    cfg.IntOpt('workers',
               default=0,
               help='The number of worker processes for handling requests'),
    cfg.BoolOpt('daemon',
                default=False,
                help='Daemonize the Gunicorn process'),
    cfg.StrOpt('accesslog',
               default=None,
               help='The Access log file to write to.'
                    '"-" means log to stderr.'),
    cfg.StrOpt('loglevel',
               default='info',
               help='The granularity of Error log outputs.',
               choices=('debug', 'info', 'warning', 'error', 'critical')),
    cfg.BoolOpt('ignore-healthcheck-accesslog',
                default=False),
    cfg.IntOpt('timeout',
               default=30,
               help='Workers silent for more than this many seconds are '
                    'killed and restarted.'),
    cfg.StrOpt('worker-class',
               default='sync',
               help='The type of workers to use.',
               choices=('sync', 'eventlet', 'gevent', 'tornado'))
], 'gunicorn')


class WsgiNotInitialized(DnsdbException):
    message = "Wsgi-app was not initialized."


class QWsgiApplication(Singleton):
    version = 'v0.1'

    def init_app(self):
        self.wsgi_app = None

    def _debug_run(self):
        self.flask_app.debug = True
        CONF.debug = True
        run_simple(CONF.web.bind,
                   CONF.web.port,
                   self.wsgi_app,
                   use_reloader=CONF.debug,
                   use_debugger=CONF.debug)

    def _gunicorn_run(self):
        from gunicorn.app.base import Application
        app = self.wsgi_app

        class QgGunicornApp(Application):

            def init(self, parser, opts, args):
                workers = CONF.gunicorn.workers
                if workers <= 0:
                    workers = multiprocessing.cpu_count() * 2 + 1
                logger_class = "simple"
                if CONF.gunicorn.ignore_healthcheck_accesslog:
                    logger_class = "qg.web.glogging.GunicornLogger"
                return {
                    'bind': '{0}:{1}'.format(CONF.web.bind, CONF.web.port),
                    'config': CONF.gunicorn.config,
                    'workers': workers,
                    'daemon': CONF.gunicorn.daemon,
                    'accesslog': CONF.gunicorn.accesslog,
                    'loglevel': CONF.gunicorn.loglevel,
                    'timeout': CONF.gunicorn.timeout,
                    'worker_class': CONF.gunicorn.worker_class,
                    'logger_class': logger_class
                }

            def load(self):
                return app

        # NOTE(zhen.pei): 为了不让gunicorn默认匹配sys.argv[1:]
        sys.argv = [sys.argv[0]]
        QgGunicornApp().run()

    def run(self):
        if CONF.web.run_mode == "werkzeug":
            self._debug_run()
        elif CONF.web.run_mode == "gunicorn":
            self._gunicorn_run()

    def append_wsgi_middlewares(self, *middlewares):
        if self.wsgi_app is None:
            raise WsgiNotInitialized
        for middleware in middlewares:
            self.wsgi_app = middleware(self.wsgi_app)
        return self

    def set_wsgi_app(self, app, base_url=None):
        if base_url is None:
            base_url = self.base_url
        if base_url != "/":
            self.wsgi_app = DispatcherMiddleware(simple_404_app, {
                base_url: app
            })
        else:
            self.wsgi_app = app


def simple_404_app(environ, start_response):
    status = '404 NOT FOUND'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [u"Page not found.".encode('utf8')]


class QFlaskApplicationError(DnsdbException):
    message = "QFlaskApplication Error"


class QFlaskApplication(Singleton):
    version = '0.1'

    def init_app(self):
        self.flask_app = None
        self.init_flask_app()

    def _set_base_url(self, base_url):
        base_url = base_url.strip()
        if not base_url.startswith("/"):
            base_url = "/" + base_url
        self.base_url = base_url

    def set_wsgi_app(self, app, base_url=None):
        if base_url is None:
            base_url = self.base_url
        if base_url != "/":
            self.wsgi_app = DispatcherMiddleware(simple_404_app, {
                base_url: app
            })
        else:
            self.wsgi_app = app

    def configure(self):
        cfg.CONF(sys.argv[1:], project=self.__class__.__name__, version=self.version,
                 default_config_files=None)
        self._set_base_url(CONF.web.base_url)
        self.set_wsgi_app(self.flask_app)

    def init_flask_app(self, flask_args=None, flask_kwargs=None):
        # init flask arguments
        flask_args = [] if flask_args is None else flask_args
        flask_kwargs = {} if flask_kwargs is None else flask_kwargs
        flask_args.insert(0, self.name)
        # create flask application
        self.flask_app = Flask(*flask_args, **flask_kwargs)
        self.flask_app.debug = CONF.debug
        self.flask_app.config['PROPAGATE_EXCEPTIONS'] = True

    def register_blueprint(self, *args, **kwargs):
        self.flask_app.register_blueprint(*args, **kwargs)

    @property
    def name(self):
        return self.__class__.__name__
