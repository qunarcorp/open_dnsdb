# -*- coding: utf-8 -*-

import os
import sys
from datetime import timedelta

from oslo_config import cfg

CONF = cfg.CONF

CONF.register_opts([
    cfg.StrOpt('log-dir'),
    cfg.StrOpt('log-file'),
    cfg.StrOpt('debug'),
    cfg.StrOpt('verbose'),
], 'log')

CONF.register_opts([
    cfg.StrOpt('connection'),
    cfg.StrOpt('data'),
], 'DB')

CONF.register_opts([
    cfg.StrOpt('server'),
    cfg.StrOpt('port'),
    cfg.StrOpt('from_addr'),
    cfg.StrOpt('password', default=''),
    cfg.StrOpt('info_list'),
    cfg.StrOpt('alert_list'),
], 'MAIL')

CONF.register_opts([
    cfg.StrOpt('allow_ip'),
    cfg.StrOpt('secret_key'),
    cfg.StrOpt('env'),
    cfg.StrOpt('header_template', default='../etc/template/zone_header')
], 'etc')

CONF.register_opts([
    cfg.IntOpt('dnsupdater_port'),
], 'api')

CONF.register_opts([
    cfg.StrOpt('acl_groups'),
    cfg.IntOpt('cname_ttl'),
    cfg.StrOpt('view_zone'),
    cfg.DictOpt('normal_view'),
    cfg.DictOpt('normal_cname'),
], 'view')

CONF.register_opts([
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
    cfg.BoolOpt('debug',
                default=False),
], 'web')

CONF.register_opts([
    cfg.StrOpt('config',
               default=None,
               help='The path to a Gunicorn config file.'),
    cfg.StrOpt('bind',
               default='127.0.0.1:8888'),
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


def setup_config(app_env, app_kind, conf_dir):
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    else:
        args = []

    common_config_file = os.path.join(conf_dir, "etc/{}/common.conf".format(app_env))
    default_config_files = [common_config_file]
    app_config_file = os.path.join(conf_dir, "etc/{}/{}.conf".format(app_env, app_kind))
    default_config_files.append(app_config_file)
    CONF(default_config_files=default_config_files, args=args)


class Config(object):
    def __init__(self, app_env, app_kind, conf_dir):
        # print 'conf_dir: ', conf_dir
        if "--" in sys.argv:
            args = sys.argv[sys.argv.index("--") + 1:]
        else:
            args = []

        common_config_file = os.path.join(conf_dir, "etc/{}/common.conf".format(app_env))
        default_config_files = [common_config_file]
        app_config_file = os.path.join(conf_dir, "etc/{}/{}.conf".format(app_env, app_kind))
        default_config_files.append(app_config_file)
        CONF(default_config_files=default_config_files, args=args)

        self.SECRET_KEY = os.environ.get('SECRET_KEY') or CONF.etc.secret_key
        self.SQLALCHEMY_DATABASE_URI = CONF.DB.connection
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # SECRET_KEY = os.environ.get('SECRET_KEY') or CONF.etc.secret_key
    # SQLALCHEMY_DATABASE_URI = CONF.DB.connection
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # PERMANENT_SESSION_LIFETIME = timedelta(days=1)
