# -*- coding: utf-8 -*-

import json

from flask import (Blueprint, redirect, url_for)
from flask_login import current_user

from dnsdb.constant.operation_type import operation_type_dict, filed_dict
from dnsdb_common.dal.operation_log import OperationLogDal
from dnsdb_common.dal.view_isp_acl import ViewIspAclDal
from dnsdb_common.dal.view_migrate import MigrateDal
from dnsdb_common.dal.view_record import ViewRecordDal
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb import deploy

bp = Blueprint('preview', 'preview')


@bp.before_request
def require_authorization():
    if not current_user.is_authenticated:
        redirect(url_for('auth.login'))


@bp.route('/list/operation_constant', methods=['GET'])
@resp_wrapper_json
def list_operationtype():
    return {'type_dict': operation_type_dict, 'filed_dict': filed_dict}


@bp.route('/get/dns_log_detail', methods=['GET'])
@parse_params([dict(name='id', type=int, required=True, nullable=False)])
@resp_wrapper_json
def get_dns_log_detail(id):
    OperationLogDal.get_log_detail(id)


@bp.route('/list/operation_log', methods=['GET'])
@parse_params([dict(name='page', type=int, required=True, nullable=False),
               dict(name='page_size', type=int, required=True, nullable=False),
               dict(name='start_time', type=str, required=False),
               dict(name='end_time', type=str, required=False),
               dict(name='domain', type=str, required=False),
               dict(name='type', type=str, required=False),
               dict(name='rtx_id', type=str, required=False),
               ])
@resp_wrapper_json
def list_operation_log(**kwargs):
    return OperationLogDal.list_operation_log(kwargs)


@bp.route('retry_deploy_job', methods=['POST'])
@parse_params([dict(name='deploy_id', type=int, required=True, nullable=False)], need_username=True)
@resp_wrapper_json
def retry_deploy_job(deploy_id, username):
    return deploy.retry_deploy_job(deploy_id, username)


@bp.route('/get/previewinfo', methods=['GET'])
@resp_wrapper_json
def get_previewinfo():
    trans = MigrateDal.get_isp_trans()
    domain_count = ViewRecordDal.zone_domain_count()
    migrate_list = []
    histories = MigrateDal.get_migrated_history()
    for history in histories:
        migrate_list.append({
            'migrate_rooms': sorted(json.loads(history.migrate_rooms)),
            'dst_rooms': sorted(json.loads(history.dst_rooms)),
            'migrate_isps': sorted([trans[isp] for isp in json.loads(history.migrate_isps)])
        })

    migrate_acl_subnet = ViewIspAclDal.get_migrate_subnet()

    return {'domain_count': domain_count,
            'migrate': migrate_list,
            'acl_migrate': migrate_acl_subnet}
