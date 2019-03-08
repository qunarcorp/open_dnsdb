# -*- coding: utf-8 -*-

from flask import (Blueprint, request)
from flask_login import login_required

from dnsdb import migrate
from dnsdb_common.dal.view_migrate import MigrateDal
from dnsdb_common.dal.view_record import ViewRecordDal
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json

bp = Blueprint('view_record', 'view_record')


@bp.before_request
@login_required
def require_authorization():
    pass


def add_view_domain_log(result, username, domain_name, rooms=None, cnames=None):
    op_after = {}
    if rooms:
        op_after.update(rooms)
    if cnames:
        op_after.update(cnames)
    return domain_name, result if result else {}, op_after


def delete_view_domain_log(result, domain_name):
    return domain_name, result, {}


def update_view_state_log(result, domain_name, isps):
    after = {}
    for isp, conf in isps.items():
        after[isp] = {}
        if 'rooms' in conf:
            after[isp] = conf['rooms']
        if 'cdn' in conf:
            after[isp] = conf['cdn']
    return domain_name, result, after


def migrate_rooms_log(result, **kwargs):
    history_info = result[0]
    before = {'src_rooms': history_info['migrate_rooms'], 'isps': history_info['migrate_isps']}
    return 'migrate_rooms', before, {'dst_rooms': history_info['dst_rooms']}

def recover_rooms_log(result, **kwargs):
    return 'recover_rooms', {}, {}


@bp.route('/add/view_domain', methods=['POST'])
@parse_params([dict(name='rooms', type=dict, required=False, nullable=False),
               dict(name='domain_name', type=str, required=True, nullable=False),
               dict(name='cnames', type=dict, required=False, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('add_view_domain', get_op_info=add_view_domain_log)
def add_view_domain(username, domain_name, rooms=None, cnames=None):
    return ViewRecordDal.upsert_view_domain(username, domain_name, rooms, cnames, "insert")


@bp.route('/update/view_domain', methods=['POST'])
@parse_params([dict(name='rooms', type=dict, required=False, nullable=False),
               dict(name='domain_name', type=str, required=True, nullable=False),
               dict(name='cnames', type=dict, required=False, nullable=False)], need_username=True)
@resp_wrapper_json
@add_web_opration_log('update_view_domain', get_op_info=add_view_domain_log)
def update_view_domain(username, domain_name, rooms=None, cnames=None):
    return ViewRecordDal.upsert_view_domain(username, domain_name, rooms, cnames, "update")


@bp.route('/delete/view_domain', methods=['POST'])
@parse_params([dict(name='domain_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_view_domain', get_op_info=delete_view_domain_log)
def delete_view_domain(domain_name):
    view_domain, record_dict = ViewRecordDal.get_domain_name_record(domain_name)
    ViewRecordDal.delete_view_domain(view_domain)
    return record_dict


@bp.route('update/view_domain_state', methods=['POST'])
@parse_params([dict(name='domain_name', type=str, required=True, nullable=False),
               dict(name='isps', type=dict, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('update_view_state', get_op_info=update_view_state_log)
def update_view_domain_state(domain_name, isps):
    return ViewRecordDal.update_view_domain_state(domain_name, isps)


@bp.route('/list/server_room', methods=['GET'])
@resp_wrapper_json
def list_server_room():
    return [item.colo_name for item in ViewRecordDal.list_server_room(colo_group='view')]


@bp.route('/list/view_domain', methods=['POST'])
@resp_wrapper_json
def list_domain_name():
    json_data = request.get_json(force=True)
    domain_name = json_data.get('domain_name', '').strip()
    server_rooms = json_data.get("server_rooms", [])
    isps = json_data.get("isps", [])
    select_cdn = json_data.get("select_cdn", True)
    return ViewRecordDal.search_view_domain(domain_name, server_rooms, isps, select_cdn)


@bp.route('/get/view_domain_info', methods=['GET'])
@parse_params([dict(name='domain_name', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_view_domain_info(domain_name):
    return ViewRecordDal.get_view_domain_info(domain_name)


@bp.route('/list_migrate_domain', methods=['POST'])
@resp_wrapper_json
def list_migrate_domain():
    json_data = request.get_json(force=True)
    src_rooms = json_data.get('src_rooms', [])
    dst_rooms = json_data.get("dst_rooms", [])
    isps = json_data.get("isps", [])
    return MigrateDal.list_migrate_domain(src_rooms, dst_rooms, isps)


@bp.route('/migrate_rooms', methods=['POST'])
@parse_params([], need_username=True)
@resp_wrapper_json
@add_web_opration_log('migrate_rooms', get_op_info=migrate_rooms_log)
def migrate_rooms(username):
    json_data = request.get_json(force=True)
    src_rooms = json_data.get('src_rooms', [])
    dst_rooms = json_data.get("dst_rooms", [])
    isps = json_data.get("isps", [])
    return migrate.migrate_rooms(src_rooms, dst_rooms, isps, username)


@bp.route('/onekey_recover_rooms', methods=['POST'])
@resp_wrapper_json
@add_web_opration_log('recover_rooms', get_op_info=recover_rooms_log)
def onekey_recover_rooms():
    return MigrateDal.onekey_recover_rooms()


@bp.route('/get/migrate_info', methods=['GET'])
@parse_params([dict(name='history_id', type=int, required=True, nullable=False)])
@resp_wrapper_json
def get_migrate_info(history_id):
    return migrate.get_migrate_info(history_id)


@bp.route('/list/migrate_history', methods=['GET'])
@resp_wrapper_json
def list_migrate_history():
    return migrate.list_migrate_history()


@bp.route('/get/view_migrate_detail', methods=['GET'])
@parse_params([dict(name='migrate_id', type=int, required=True, nullable=False),
               dict(name='page', type=int, required=True, nullable=False),
               dict(name='page_size', type=int, required=True, nullable=False),
               dict(name='domain', type=str, required=True, nullable=False)])
@resp_wrapper_json
def get_view_migrate_detail(migrate_id, domain, page, page_size):
    return MigrateDal.get_view_migrate_detail(migrate_id, domain, page, page_size)

