# -*- coding: utf-8 -*-


from flask import (Blueprint)

from dnsdb_common.dal.host_group_conf import HostGroupConfDal
from dnsdb_common.dal.zone_record import ZoneRecordDal
from dnsdb_common.dal.operation_log import OperationLogDal
from dnsdb_common.dal.view_isp_acl import ViewIspAclDal
from dnsdb_common.library.decorators import authenticate
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json

bp = Blueprint('api', 'api')


@bp.before_request
@authenticate
def require_authorization():
    pass


@bp.route('/get/reload_status', methods=['GET'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_reload_status(group_name):
    return HostGroupConfDal.get_group_by_name(group_name).reload_status


@bp.route('/get/host_group', methods=['GET'])
@parse_params([dict(name='host_ip', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_host_group(host_ip):
    return HostGroupConfDal.get_group_by_ip(host_ip)


@bp.route('/get/named_conf', methods=['GET'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_group_named(group_name):
    return HostGroupConfDal.build_complete_named_conf(group_name)


@bp.route('/update/host_conf_md5', methods=['POST'])
@parse_params([dict(name='host_ip', type=str, required=True, nullable=False),
               dict(name='host_conf_md5', type=str, required=True, nullable=False)])
@resp_wrapper_json
def update_host_conf_md5(host_ip, host_conf_md5):
    return HostGroupConfDal.update_host_conf_md5(host_ip, host_conf_md5)


@bp.route('/get/acl_file', methods=['GET'])
@parse_params([dict(name='acl_file', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_acl_file_content(acl_file):
    return ViewIspAclDal.get_acl_file_content(acl_file)


@bp.route('/update/deploy_info', methods=['POST'])
@parse_params([dict(name='deploy_id', type=int, required=True, nullable=False),
               dict(name='host', type=str, required=True, nullable=False),
               dict(name='is_success', type=bool, required=True, nullable=False),
               dict(name='msg', type=str, required=True, nullable=False)])
@resp_wrapper_json
def update_deploy_info(deploy_id, host, is_success, msg):
    OperationLogDal.update_deploy_info(deploy_id, host, is_success, msg)


@bp.route('/get/update_zones', methods=['GET'])
@parse_params([dict(name='group_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_update_zones(group_name):
    return ZoneRecordDal.get_zone_need_update(group_name)


@bp.route('/get/zone_info', methods=['GET'])
@parse_params([dict(name='zone_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_zone_info(zone_name):
    zone_info = ZoneRecordDal.get_zone_header(zone_name)
    zone_info['records'] = ZoneRecordDal.get_zone_records(zone_name)
    return zone_info

@bp.route('/update/zone_serial', methods=['POST'])
@parse_params([dict(name='zone_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def update_zone_serial(zone_name):
    return ZoneRecordDal.update_serial_num(zone_name)
