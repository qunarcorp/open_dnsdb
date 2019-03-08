# -*- coding: utf-8 -*-

from flask import (Blueprint)
from oslo_config import cfg

from dns_updater.api.worker import start_update_thread
from dns_updater.utils.updater_util import send_alarm_email
from dnsdb_common.library.decorators import authenticate
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json

CONF = cfg.CONF

bp = Blueprint('api', 'api')


@bp.route('/notify_update/named', methods=['POST'])
@authenticate
@parse_params([dict(name='group_name', type=str, required=True, nullable=False),
               dict(name='group_conf_md5', type=str, required=True, nullable=False)])
@resp_wrapper_json
def update_named(group_name, group_conf_md5):
    if group_name != CONF.host_group:
        return send_alarm_email(
            u'Host %s group not match: local %s, param: %s' % (CONF.host_ip, CONF.host_group, group_name))
    start_update_thread('named.conf', group_conf_md5=group_conf_md5, group_name=group_name)
    return


@bp.route('/notify_update', methods=['POST'])
@authenticate
@parse_params([dict(name='update_type', type=str, required=True, nullable=False),
               dict(name='group_name', type=str, required=True, nullable=False),
               dict(name='params', type=dict, required=True, nullable=False)])
@resp_wrapper_json
def update_conf(update_type, group_name, params):
    start_update_thread(update_type, group_name=group_name, **params)
    return
