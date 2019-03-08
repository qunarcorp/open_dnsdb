# -*- coding: utf-8 -*-

import re

from flask import (Blueprint)
from flask_login import current_user, login_required

from dnsdb.constant.constant import RE_PATTERN
from dnsdb_common.dal.user import UserDal
from dnsdb_common.library.decorators import add_web_opration_log
from dnsdb_common.library.decorators import parse_params
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import BadParam

bp = Blueprint('user', 'user')


def _is_valid_user(user):
    ptn = re.search(RE_PATTERN['username'], user)
    if ptn is None:
        return False
    if len(ptn.groups()) == 0:
        return False
    return ptn.group(1) == user


def get_add_info(result, **kwargs):
    op_after = kwargs.copy()
    op_after.pop('password', None)
    role_id = op_after.pop('role_id')
    op_after['role'] = UserDal.get_role_name(role_id)
    return kwargs['username'], {}, op_after


def get_update_info(result, **kwargs):
    op_after = kwargs.copy()
    op_after.pop('password', None)
    role_id = op_after.pop('role_id')
    op_after['role'] = UserDal.get_role_name(role_id)
    return kwargs['username'], {}, op_after


def get_delete_info(result, **kwargs):
    username = kwargs['username']
    return username, result, {}


@bp.route('/roles', methods=['GET'])
@login_required
@resp_wrapper_json
def get_roles():
    return UserDal.get_roles()


@bp.route('/get', methods=['GET'])
@login_required
@parse_params([dict(name='username', type=str, required=False, nullable=False)])
@resp_wrapper_json
def get_user(username):
    user = UserDal.get_user_info(username=username)
    if user is None:
        return []
    return [UserDal.get_user_info(username=username).json_serialize()]


@bp.route('/list', methods=['GET'])
@login_required
@parse_params([dict(name='page', type=int, required=True, nullable=False),
               dict(name='page_size', type=int, required=True, nullable=False),
               dict(name='role_id', type=str, required=False, nullable=False)])
@resp_wrapper_json
def list_user(**kwargs):
    return UserDal.list_user(**kwargs)


@bp.route('/add', methods=['POST'])
@login_required
@parse_params([dict(name='username', type=str, required=True, nullable=False),
               dict(name='email', type=str, required=True, nullable=False),
               dict(name='password', type=str, required=True, nullable=False),
               dict(name='role_id', type=int, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('add_user', get_op_info=get_add_info)
def add_user(username, email, password, role_id):
    UserDal.add_user(username, email, password, role_id)


@bp.route('/delete', methods=['POST'])
@login_required
@parse_params([dict(name='username', type=str, required=True, nullable=False)])
@resp_wrapper_json
@add_web_opration_log('delete_user', get_op_info=get_delete_info)
def delete_user(username):
    if username == current_user.username:
        raise BadParam('cannot delete yourself')
    user = UserDal.get_user_info(username=username)
    if not user:
        raise BadParam('No such user with name: %s' % username)
    result = user.json_serialize(include=('username', 'email', 'role'))
    UserDal.delete_user(username)
    return result
