# -*- coding: utf-8 -*-

from flask import (Blueprint, redirect, url_for, request)
from flask_login import current_user

from dnsdb_common.dal.host_group_conf import HostGroupConfDal
from dnsdb_common.dal.zone_record import ZoneRecordDal
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import BadParam

bp = Blueprint('config', 'config')


@bp.before_request
def require_authorization():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))


def add_host_group_log(result, **kwargs):
    group_name, hosts = result
    op_after = {'hosts': ['{} {}'.format(item['host_name'], item['host_ip']) for item in hosts]}
    return group_name, {}, op_after


def delete_host_group_log(result, group_name):
    op_before = {'hosts': result}
    return group_name, op_before, {}


def add_host_log(result, group_name, host_name, host_ip):
    return group_name, {}, {'hostname': host_name, 'ip': host_ip}


def delete_host_log(result, group_name, host_name):
    return group_name, {}, {'hostname': host_name}


def update_named_log(result, **kwargs):
    return kwargs['name'], {}, {'md5': result[0], 'deploy_job': result[1]}

def update_reload_log(result, group_name, reload_status):
    return group_name, {}, {'status': reload_status}


def add_name_zone_log(result, **kwargs):
    op_after = kwargs['conf']
    op_after['deploy_job'] = result
    return kwargs['zone'], {}, op_after

def delete_name_zone_log(result, **kwargs):
    return kwargs['zone'], result[0], {'deploy_job': result[1]}

def update_zone_header_log(result):
    return result[0], {}, {'serial_num': result[1]}

def _check_and_format_params(group_name, hosts):
    group_name = group_name.strip()
    if group_name.endswith('Master'):
        group_type = 'master'
    elif group_name.endswith('Slave'):
        group_type = 'slave'
    else:
        raise BadParam('Group name must endswith Slave or Master')
    for item in hosts:
        item['host_name'] = item['host_name'].strip()
        item['host_ip'] = item['host_ip'].strip()
        HostGroupConfDal.check_host(item['host_name'], item['host_ip'])

        item['host_group'] = group_name

    return group_name, group_type, hosts


@bp.route('/add/host_group', methods=['POST'])
@resp_wrapper_json
@add_web_opration_log('add_host', get_op_info=add_host_group_log)
def add_host_group():
    params = request.get_json(force=True)
    group_name, group_type, hosts = _check_and_format_params(params['group_name'], params['hosts'])
    HostGroupConfDal.add_host_group(group_name, group_type, hosts)
    return group_name, hosts


@bp.route('/delete/host_group', methods=['POST'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_host', get_op_info=delete_host_group_log)
def delete_host_group(group_name):
    return HostGroupConfDal.delete_host_group(group_name)


@bp.route('/add/host', methods=['POST'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False),
               dict(name='host_name', type=str, required=True, nullable=False),
               dict(name='host_ip', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('add_host', get_op_info=add_host_log)
def add_host(group_name, host_name, host_ip):
    HostGroupConfDal.check_host(host_name, host_ip)
    return HostGroupConfDal.add_host(group_name, host_name, host_ip)


@bp.route('/delete/host', methods=['POST'])
@parse_params([dict(name='host_name', type=str, required=True, nullable=False),
               dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_host', get_op_info=delete_host_log)
def delete_host(group_name, host_name):
    return HostGroupConfDal.delete_host(group_name, host_name)


@bp.route('/list/host_group', methods=['GET'])
@resp_wrapper_json
def list_host_group():
    return HostGroupConfDal.list_host_group()


@bp.route('/get/named_conf_header', methods=['GET'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_named_conf(group_name):
    return HostGroupConfDal.get_named_conf_header(group_name)


@bp.route('/update/group_reload_status', methods=['POST'])
@parse_params([dict(name='reload_status', type=bool, required=True, nullable=False),
               dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('update_reload_status', get_op_info=update_reload_log)
def update_group_reload_status(group_name, reload_status):
    if not HostGroupConfDal.update_group_reload_status(group_name, reload_status):
        raise BadParam('No such group', msg_ch=u'没有主机组:%s' % group_name)


@bp.route('/update/named_conf_header', methods=['POST'])
@parse_params([dict(name='name', type=str, required=True, nullable=False),
               dict(name='conf_content', type=str, required=True, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('update_named_conf_header', get_op_info=update_named_log)
def update_named_conf(name, conf_content, username):
    return HostGroupConfDal.update_named_conf(name, conf_content, username)


@bp.route('/get/has_named_group', methods=['GET'])
@resp_wrapper_json
def get_host_group():
    group = []
    for item in HostGroupConfDal.list_host_group():
        if item['has_conf']:
            group.append({'group_name': item['group_name']})
    return group


@bp.route('/list/named_zone', methods=['GET'])
@resp_wrapper_json
def list_named_zone():
    return HostGroupConfDal.list_named_zone()


@bp.route('/get/named_zone', methods=['GET'])
@parse_params([dict(name='zone_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_named_zone(zone_name):
    return HostGroupConfDal.get_named_zone(zone_name)


@bp.route('/check_named_zone', methods=['POST'])
@parse_params([dict(name='zone', type=str, required=True, nullable=False),
               dict(name='conf', type=dict, required=True, nullable=False)])
@resp_wrapper_json
def check_named_zone(zone, conf):
    for group, zone_conf in conf.iteritems():
        HostGroupConfDal.check_zone_conf(group, zone, zone_conf)


@bp.route('/add/named_zone', methods=['POST'])
@parse_params([dict(name='zone', type=str, required=True, nullable=False),
               dict(name='zone_type', type=int, required=True, nullable=False),
               dict(name='conf', type=dict, required=True, nullable=False),
               dict(name='add_header', type=bool, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('add_named_zone', get_op_info=add_name_zone_log)
def add_named_zone(zone, zone_type, conf, add_header, username):
    return HostGroupConfDal.add_named_zone(zone, zone_type, conf, add_header, username)


@bp.route('/update/named_zone', methods=['POST'])
@parse_params([dict(name='zone', type=str, required=True, nullable=False),
               dict(name='zone_type', type=int, required=True, nullable=False),
               dict(name='conf', type=dict, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('update_named_zone', get_op_info=add_name_zone_log)
def update_named_zone(zone, zone_type, conf, username):
    return HostGroupConfDal.update_named_zone(zone, zone_type, conf, username)


@bp.route('/delete/named_zone', methods=['POST'])
@parse_params([dict(name='zone', type=str, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('delete_named_zone', get_op_info=delete_name_zone_log)
def delete_named_zone(zone, username):
    return HostGroupConfDal.delete_named_zone(zone, username)


@bp.route('/list/zone_header', methods=['GET'])
@resp_wrapper_json
def list_zone_header():
    return ZoneRecordDal.list_zone_header()


@bp.route('/get/zone_header', methods=['GET'])
@parse_params([dict(name='zone_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_zone_header(zone_name):
    return ZoneRecordDal.get_zone_header(zone_name)


@bp.route('/check_zone_header', methods=['POST'])
@resp_wrapper_json
def check_zone_header():
    params = request.get_json(force=True)
    return ZoneRecordDal.check_zone_header(params['zone_name'], params['header_content'])

@bp.route('/update/zone_header', methods=['POST'])
@resp_wrapper_json
@add_web_opration_log('update_zone_header', get_op_info=update_zone_header_log)
def update_zone_header():
    params = request.get_json(force=True)
    serial_num = ZoneRecordDal.update_zone_header(params['zone_name'], params['header_content'])
    return params['zone_name'], serial_num

