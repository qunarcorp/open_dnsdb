# -*- coding: utf-8 -*-

from flask import (Blueprint, request)
from flask_login import login_required

from dnsdb_common.dal.view_isp_acl import ViewIspAclDal
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import BadParam
from dnsdb_common.library.validator import valid_string

bp = Blueprint('view', 'view')


@bp.before_request
@login_required
def require_authorization():
    pass


def _validate_args(param_dict):
    validator_param = {
        "name_in_english": dict(max_len=32, pattern='[a-zA-Z_]+'),
        "name_in_chinese": dict(max_len=32),
        "acl_name": dict(max_len=16, pattern='[a-zA-Z]+', allow_blank=True),
        "abbreviation": dict(max_len=8, pattern='[a-z]+'),
        "acl_file": dict(max_len=16, pattern='[a-zA-Z\.]+', allow_blank=True),
    }

    param = {}
    for k, v in validator_param.iteritems():
        ok, format_str = valid_string(param_dict[k], **v)
        if not ok:
            raise BadParam(u'param validate error: %s, %s' % (k, v), msg_ch=u'%s: %s' % (k, format_str))
        if format_str:
            param[k] = format_str
    return param


def add_isp_log(result, **kwargs):
    domain = result.pop('name_in_english')
    result.pop('username', None)
    return domain, {}, result


def delete_isp_log(result, **kwargs):
    domain = kwargs['name_in_english']
    return domain, {}, {}


def update_isp_log(result, **kwargs):
    domain = kwargs['name_in_english']
    return domain, {}, kwargs['update_data']

def acl_migration_log(result, **kwargs):
    subnet = result.pop('subnet', kwargs['acl_subnet_id'])
    return subnet, {}, result

def add_acl_subnet_log(result, subnet, acl, username):
    return acl, {}, {'subnet': subnet}

def delete_acl_subnet_log(result, **kwargs):
    return result['origin_acl'] , {}, {'subnet': result['subnet']}


@bp.route('/add/isp', methods=['POST'])
@parse_params([], need_username=True)
@resp_wrapper_json
@add_web_opration_log('add_isp', get_op_info=add_isp_log)
def add_isp(username):
    params = request.get_json(force=True)
    data = _validate_args(params)
    data['username'] = username
    ViewIspAclDal.add_isp(data)
    return data


@bp.route('/delete/isp', methods=['POST'])
@parse_params([dict(name='name_in_english', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_isp', get_op_info=delete_isp_log)
def delete_isp(name_in_english):
    count = ViewIspAclDal.delete_isp(name_in_english)
    if count == 0:
        raise BadParam('No such isp: %s' % name_in_english, msg_ch=u'没有对应的运营商记录')


@bp.route('/update/isp', methods=['POST'])
@parse_params([dict(name='name_in_english', type=str, required=True, nullable=False),
               dict(name='update_data', type=dict, required=True, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('update_isp', get_op_info=update_isp_log)
def update_isp(name_in_english, update_data, username):
    count = ViewIspAclDal.update_isp(name_in_english, update_data, username)
    if count == 0:
        raise BadParam('No such isp: %s' % name_in_english, msg_ch=u'没有对应的运营商记录')

@bp.route('/migrate_subnet_acl', methods=['POST'])
@parse_params([dict(name='acl_subnet_id', type=int, required=True, nullable=False),
               dict(name='to_acl', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('acl_migration', get_op_info=acl_migration_log)
def migrate_subnet_acl(acl_subnet_id, to_acl):
    return ViewIspAclDal.migrate_acl(acl_subnet_id, to_acl)

@bp.route('/add/acl_subnet', methods=['POST'])
@parse_params([dict(name='subnet', type=str, required=True, nullable=False),
               dict(name='acl', type=str, required=True, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('add_acl_subnet', get_op_info=add_acl_subnet_log)
def add_acl_subnet(subnet, acl, username):
    return ViewIspAclDal.add_acl_subnet(subnet, acl, username)

@bp.route('/delete/acl_subnet', methods=['POST'])
@parse_params([dict(name='subnet_id', type=int, required=True, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('delete_acl_subnet', get_op_info=delete_acl_subnet_log)
def delete_acl_subnet(subnet_id, username):
    return ViewIspAclDal.delete_acl_subnet(subnet_id, username)


@bp.route('/list/isp', methods=['GET'])
@resp_wrapper_json
def list_isp():
    return ViewIspAclDal.list_isp()

@bp.route('/list/acl_subnet_by_ip', methods=['GET'])
@parse_params([dict(name='ip', type=str, required=True, nullable=False)])
@resp_wrapper_json
def list_acl_subnet_by_ip(ip):
    return ViewIspAclDal.list_acl_subnet_by_ip(ip)

@bp.route('/list/acl_isp_info', methods=['GET'])
@resp_wrapper_json
def list_acl_isp_info():
    return ViewIspAclDal.list_acl_isp()


@bp.route('/list/migrate_subnet', methods=['GET'])
@resp_wrapper_json
def list_migrate_subnet():
    return ViewIspAclDal.get_migrate_subnet()



