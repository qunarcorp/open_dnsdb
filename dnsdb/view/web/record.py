# -*- coding: utf-8 -*-

import re

from flask import (Blueprint)
from flask_login import login_required

from dnsdb_common.dal.subnet_ip import SubnetIpDal
from dnsdb_common.dal.zone_record import ZoneRecordDal
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import BadParam
from dnsdb_common.library.utils import is_valid_cname
from dnsdb_common.library.utils import is_valid_domain_name
from dnsdb_common.library.utils import is_valid_ip_format

bp = Blueprint('record', 'record')


@bp.before_request
@login_required
def require_authorization():
    pass


def add_record_log(result, **kwargs):
    domain = kwargs.pop('domain')
    kwargs.pop('username')
    kwargs['serial_num'] = result
    return domain, {}, kwargs


def modify_record_log(result, **kwargs):
    domain = kwargs['domain_name']
    op_after = kwargs['update_dict']
    op_after['serial_num'] = result
    return domain, {'record': kwargs['origin_record']}, op_after


def delete_record_log(result, **kwargs):
    domain = kwargs.pop('domain_name')
    kwargs['serial_num'] = result
    return domain, kwargs, {}


def _validate_args(domain_name, param_dict):
    is_valid_domain_name(domain_name)
    if param_dict.get('ttl', 0) < 0:
        raise BadParam("Invalid ttl.", msg_ch=u'ttl必须大于等于0')
    record_type = param_dict.get('record_type', None)
    if record_type:
        check_record = param_dict['check_record']
        record = param_dict['record']
        if record_type == 'CNAME':
            if domain_name == param_dict['record']:
                raise BadParam("Self-CNAME is not allowed.", msg_ch=u'域名和CNAME不能相同')
            if check_record and is_valid_cname(record):
                raise BadParam('Invalid CNAME record', msg_ch=u'CNAME记录的zone必须在DNSDB管理中')
        elif record_type == 'A':
            is_valid_ip_format(record)
            if check_record and (not SubnetIpDal.is_ip_exist(record)):
                raise BadParam('No such ip %s' % record, msg_ch=u'IP在数据库中不存在')
        else:
            raise BadParam("Invalid record type.", msg_ch=u'记录类型只能是[A, CNAME]')


@bp.route('/manually_add_record', methods=['POST'])
@parse_params([dict(name='domain', type=str, required=True, nullable=False),
               dict(name='record', type=str, required=True, nullable=False),
               dict(name='record_type', type=str, required=True, nullable=False),
               dict(name='ttl', type=int, required=True, nullable=False),
               dict(name='check_record', type=bool, required=False, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('manadd_record', get_op_info=add_record_log)
def manually_add_record(domain, record, record_type, ttl, username, check_record=True):
    update_dict = dict(record_type=record_type, record=record, check_record=check_record, ttl=ttl)
    _validate_args(domain, update_dict)
    return ZoneRecordDal.add_record(domain, record, record_type, ttl, username)


@bp.route('/auto_add_record', methods=['POST'])
@parse_params([dict(name='domain', type=str, required=True, nullable=False),
               dict(name='region', type=str, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('autoadd_record', get_op_info=add_record_log)
def auto_add_record(domain, region, username):
    is_valid_domain_name(domain)
    if not SubnetIpDal.is_intranet_region(region):
        raise BadParam("Can't automatically bind an A record with public ip.", msg_ch=u'不能自动绑定A记录到公网IP')
    if ZoneRecordDal.get_domain_records(domain_name=domain):
        raise BadParam('Domain name %s has already had a record' % domain, msg_ch=u'域名已有记录, 不能自动绑定')

    return ZoneRecordDal.auto_add_record(domain, region, username)


@bp.route('/modify_record', methods=['POST'])
@parse_params([dict(name='domain_name', type=str, required=True, nullable=False),
               dict(name='origin_record', type=str, required=True, nullable=False),
               dict(name='update_dict', type=dict, required=True, nullable=False)],
              need_username=True)
@resp_wrapper_json
@add_web_opration_log('modify_record', get_op_info=modify_record_log)
def modify_record(domain_name, origin_record, update_dict, username):
    _validate_args(domain_name, update_dict)
    return ZoneRecordDal.modify_record(domain_name, origin_record, update_dict, username)


@bp.route('/delete', methods=['POST'])
@parse_params([dict(name='domain_name', type=str, required=True, nullable=False),
               dict(name='record', type=str, required=True, nullable=False),
               dict(name='record_type', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_record', get_op_info=delete_record_log)
def delete_record(domain_name, record, record_type):
    return ZoneRecordDal.delete_record(domain_name, record, record_type)


@bp.route('/get/domain_records', methods=['GET'])
@parse_params([dict(name='record', type=str, required=False, nullable=False),
               dict(name='domain_name', type=str, required=False, nullable=False)])
@resp_wrapper_json
def get_domain_records(**kwargs):
    if 'record' in kwargs:
        key = 'record'
        # return ZoneRecordDal.get_domain_records(**kwargs)
    else:
        key = 'domain_name'

    codition = kwargs[key]
    tmp = codition.replace('*', '%')

    pattern = re.search("(\[.*\])", codition)
    if pattern is not None:
        tmp = tmp.replace(pattern.group(1), '%')

    records = ZoneRecordDal.search_domain_records(key, tmp)
    # Expression with square brackets is not used, the records are satisified.
    if pattern is None or len(records) == 0:
        return records

    m = re.search("\[([0-9]*)\-([0-9]*)\]", codition)
    start = int(m.group(1))
    end = int(m.group(2))
    needed = [codition.replace(pattern.group(1), str(i)) for i in range(start, end + 1)]
    return filter(lambda x: x[key] in needed, records)


@bp.route('/list/zone_ttl', methods=['GET'])
@resp_wrapper_json
def list_zone_ttl():
    return ZoneRecordDal.list_zone_ttl()
