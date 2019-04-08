# -*- coding: utf-8 -*-

import os

from oslo_config import cfg

CONF = cfg.CONF

CONF.register_opts([
    cfg.StrOpt('env'),
    cfg.StrOpt('secret_key'),
    cfg.StrOpt('log_dir'),
    cfg.StrOpt('tmp_dir'),
    cfg.StrOpt('pidfile'),
    cfg.StrOpt('backup_dir'),
    cfg.IntOpt('zone_update_interval'),
    cfg.StrOpt('allow_ip')
], 'etc')

CONF.register_opts([
    cfg.StrOpt('dnsdbapi_url'),
], 'api')

CONF.register_opts([
    cfg.StrOpt('log-dir'),
    cfg.StrOpt('log-file'),
    cfg.StrOpt('debug'),
    cfg.StrOpt('verbose'),
], 'log')

CONF.register_opts([
    cfg.StrOpt('server'),
    cfg.StrOpt('port'),
    cfg.StrOpt('from_addr'),
    cfg.StrOpt('password', default=''),
    cfg.StrOpt('info_list'),
    cfg.StrOpt('alert_list'),
], 'MAIL')

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
               default='0.0.0.0:8888'),
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

CONF.register_opts([
    cfg.StrOpt('server'),
    cfg.StrOpt('port'),
    cfg.StrOpt('from_addr'),
    cfg.StrOpt('info_list'),
    cfg.StrOpt('alert_list'),
], 'MAIL')

CONF.register_opts([
    cfg.StrOpt('named_dir'),
    cfg.StrOpt('zone_dir'),
    cfg.StrOpt('named_checkconf'),
    cfg.StrOpt('named_zonecheck'),
    cfg.StrOpt('mkrdns'),
    cfg.StrOpt('acl_dir'),
    cfg.StrOpt('rndc'),
], 'bind_default')

CONF.register_opts([
    cfg.StrOpt('named_dir'),
    cfg.StrOpt('zone_dir'),
    cfg.StrOpt('named_checkconf'),
    cfg.StrOpt('rndc'),
], 'ViewSlave')

CONF.register_opts([
    cfg.StrOpt('named_dir'),
    cfg.StrOpt('zone_dir'),
    cfg.StrOpt('acl_dir'),
    cfg.StrOpt('named_checkconf'),
    cfg.StrOpt('rndc'),
], 'ViewMaster')

CONF.register_opts([
    cfg.StrOpt('named_dir'),
    cfg.StrOpt('zone_dir'),
    cfg.StrOpt('named_checkconf'),
    cfg.StrOpt('rndc'),
], 'Master')


def setup_config(app_env, app_kind, conf_dir):
    common_config_file = os.path.join(conf_dir, "etc/{}/common.conf".format(app_env))
    default_config_files = [common_config_file]
    app_config_file = os.path.join(conf_dir, "etc/{}/{}.conf".format(app_env, app_kind))
    default_config_files.append(app_config_file)
    CONF(default_config_files=default_config_files, args=[])

    from dns_updater.utils.updater_util import (DnsdbApi, get_self_ip)
    CONF.host_ip = get_self_ip()
    CONF.host_group = DnsdbApi.get_host_group()['data']
    setattr(CONF, 'bind_conf', CONF.bind_default)

    if getattr(CONF, CONF.host_group, None):
        for k, v in CONF[CONF.host_group].items():
            if v is not None:
                setattr(CONF.bind_conf, k, v)
