# -*- coding: utf-8 -*-


from dnsdb_common.dal.user import UserDal
from dnsdb_common.library.decorators import resp_wrapper_json
from dnsdb_common.library.exception import DnsdbException
from dnsdb_common.library.exception import Unauthorized
from flask import (Blueprint)
from flask import request
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', 'auth')


@bp.route('/login', methods=['GET', 'POST'])
@resp_wrapper_json
def login():
    if request.method == 'POST':
        form = request.get_json(force=True)
        user = UserDal.get_user_info(username=form['username'])
        if user is not None and user.verify_password(form['password']):
            login_user(user, remember=True)
            return current_user.username
        raise DnsdbException('Invalid username or password.', msg_ch=u'账号或密码错误')
    else:
        raise Unauthorized()


@bp.route('/logout', methods=['POST'])
@login_required
@resp_wrapper_json
def logout():
    logout_user()
    raise Unauthorized()


@bp.route("/logged_in_user", methods=['GET'])
@login_required
@resp_wrapper_json
def logged_in_user():
    return current_user.username
