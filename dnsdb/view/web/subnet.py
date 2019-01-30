# -*- coding: utf-8 -*-

import re

from flask import (Blueprint)
from flask_login import login_required

from dnsdb_common.dal.subnet_ip import SubnetIpDal
from dnsdb_common.library.IPy import IP
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import BadParam

bp = Blueprint('subnet', 'subnet')


@bp.before_request
@login_required
def require_authorization():
    pass


def _is_valide_region(region):
    if len(region) > 64:
        raise BadParam('The length of region should <80', msg_ch=u'名称长度必须<80')

    if not re.match(r'^[a-zA-Z0-9_]+$', region):
        raise BadParam('region only a-z,A-Z,0-9,_ allowed.', msg_ch=u'名称中只能包含大小写字母、数字、下划线')


def _validate_args(subnet, region, colo):
    if '/' not in subnet:
        raise BadParam('Invalid subnet.', msg_ch=u'请使用cidr格式的网段')
    try:
        sub = IP(subnet)
    except:
        raise BadParam('Invalid subnet.', msg_ch=u'错误的网段格式')

    prefix = sub.prefixlen()
    if prefix < 16 or prefix > 32:
        raise BadParam('Invalid subnet.', msg_ch=u'掩码长度在[16-32]之间')

    _is_valide_region(region)

    if colo not in SubnetIpDal.get_colo_by_group('subnet'):
        raise BadParam('Invalid colo', msg_ch=u'请先配置机房')


def add_subnet_log(result, **kwargs):
    return kwargs['region'], {}, {'subnet': kwargs['subnet']}


def delete_subnet_log(result, **kwargs):
    return kwargs['region'], {'subnet': kwargs['subnet']}, {}


def rename_subnet_log(result, **kwargs):
    return kwargs['new_region'], {'region': kwargs['old_region']}, {'region': kwargs['new_region']}


@bp.route('/add/subnet', methods=['POST'])
@parse_params([dict(name='subnet', type=str, required=True, nullable=False),
               dict(name='region', type=str, required=True, nullable=False),
               dict(name='colo', type=str, required=True, nullable=False),
               dict(name='comment', type=str, required=False, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('add_subnet', get_op_info=add_subnet_log)
def add_subnet(subnet, region, colo, comment, username):
    _validate_args(subnet, region, colo)
    return SubnetIpDal.add_subnet(subnet, region, colo, comment, username)


@bp.route('/delete', methods=['POST'])
@parse_params([dict(name='subnet', type=str, required=True, nullable=False),
               dict(name='region', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_subnet', get_op_info=delete_subnet_log)
def delete_subnet(subnet, region):
    return SubnetIpDal.delete_subnet(subnet, region)


@bp.route('/rename_subnet', methods=['POST'])
@parse_params([dict(name='old_region', type=str, required=True, nullable=False),
               dict(name='new_region', type=str, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('rename_subnet', get_op_info=rename_subnet_log)
def rename_subnet(old_region, new_region, username):
    _is_valide_region(new_region)
    return SubnetIpDal.rename_subnet(old_region, new_region, username)


@bp.route('/get/subnet_colos', methods=['GET'])
@resp_wrapper_json
def get_subnet_colos():
    return SubnetIpDal.get_colo_by_group('subnet')


@bp.route('get/subnet_ip', methods=['GET'])
@parse_params([dict(name='region', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_subnet_ip(region):
    return SubnetIpDal.get_subnet_ip(region)


@bp.route('/list/region', methods=['GET'])
@resp_wrapper_json
def list_region():
    return SubnetIpDal.list_region()


@bp.route('/get/region_by_ip', methods=['GET'])
@parse_params([dict(name='ip', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_region_by_ip(ip):
    return [SubnetIpDal.get_region_by_ip(ip)]


@bp.route('/get/region_by_name', methods=['GET'])
@parse_params([dict(name='region', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_region_by_name(region):
    return SubnetIpDal.get_region_by_name_like(region)
