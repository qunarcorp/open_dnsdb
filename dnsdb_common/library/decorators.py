# -*- coding: utf-8 -*-

import json
from datetime import datetime
from functools import wraps

from flask import request, Response
from flask_login import current_user
from flask_restful import reqparse, abort
from oslo_config import cfg

from ..dal.operation_log import OperationLogDal
from ..library.exception import DnsdbException
from ..library.log import getLogger
from ..library.param_validator import ParamValidator


CONF = cfg.CONF
log = getLogger(__name__)

def getRemoteAddr(s):
    if s.headers.get('X-Real-Ip') is None:
        return s.remote_addr
    else:
        return s.headers.get('X-Real-Ip')


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(func, 'authenticated', True):
            return func(*args, **kwargs)

        acct = True
        allow_list_ip = CONF.etc.allow_ip.split(',')
        if getRemoteAddr(request) not in allow_list_ip:
            acct = False
        # beta env allow any ip in
        if CONF.etc.env != 'prod':
            acct = True
        if acct:
            return func(*args, **kwargs)

        return abort(401)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(current_user)
        if not current_user.is_authenticated:
            return abort(401)
        if not current_user.is_administrator:
            return abort(403)
        return func(*args, **kwargs)

    return wrapper


def resp(code=0, data=None, message=None, is_json=True, msg_en=None):
    if is_json:
        return Response(json.dumps({
            'errcode': code,
            'data': data,
            'message': message if message else msg_en,
            'msg_en': msg_en}))

    if code == 0:
        return data, 200
    elif code == 401:
        return abort(401)
    else:
        code = code if code >= 400 else 400
        return message, code


def resp_wrapper(is_json=True):
    def _wrapper(func):
        @wraps(func)
        def decorator(*kargs, **kwargs):
            try:
                return resp(data=func(*kargs, **kwargs), is_json=is_json)
            except DnsdbException as ex:
                log.error("func: %s, args: %s, kwargs: %s" % (func.__name__, kargs, kwargs))
                log.exception(ex)
                return resp(code=ex.errcode, is_json=is_json,
                            message=ex.msg_ch,
                            msg_en=ex.message)
            except Exception as ex:
                log.error("func: %s, args: %s, kwargs: %s" % (func.__name__, kargs, kwargs))
                log.exception(ex)
                return resp(code=500, msg_en='interval error, %s' % ex, is_json=is_json)

        return decorator

    return _wrapper


resp_wrapper_raw = resp_wrapper(is_json=False)
resp_wrapper_json = resp_wrapper(is_json=True)


def parse_params(param_meta=None, need_username=False):
    parser = reqparse.RequestParser()
    param_meta = [] if param_meta is None else param_meta
    for kw in param_meta:
        parser.add_argument(**kw)

    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            params = parser.parse_args()
            for k in list(params.keys()):
                v = params[k]
                if v is None:
                    params.pop(k)
                if isinstance(v, str):
                    params[k] = v.strip()

            kwargs.update(params)
            if need_username:
                kwargs['username'] = current_user.username
            log.info('func: %s, args: %s' % (func.__name__, kwargs))
            return func(*args, **kwargs)

        return _wrapper

    return _inner


def predicate_params(param_meta=None, need_username=False):
    _param_meta = [] if param_meta is None else param_meta

    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            params = ParamValidator(_param_meta)

            kwargs.update(params)
            if need_username:
                kwargs['username'] = current_user.username
            return func(*args, **kwargs)

        return _wrapper

    return _inner


def add_opration_log(op_type, before_func, after_func):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            rtx_id, op_domain, op_before, op_after = before_func(*args, **kwargs)
            try:
                ret = func(*args, **kwargs)
                op_after.update(after_func(ret))
                OperationLogDal.insert_operation_log_with_dict(rtx_id, op_domain, op_type,
                                                               op_before,
                                                               op_after, 'ok')
            except Exception as ex:
                OperationLogDal.insert_operation_log_with_dict(rtx_id, op_domain, op_type,
                                                               op_before,
                                                               op_after, 'fail', ex.message)
                raise
            return ret

        return _wrapper

    return _inner


def add_web_opration_log(op_type, get_op_info):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            rtx_id = current_user.username
            try:
                ret = func(*args, **kwargs)
                op_domain, op_before, op_after = get_op_info(result=ret, *args, **kwargs)
                if op_domain is None:
                    op_domain = op_type
                OperationLogDal.insert_operation_log_with_dict(rtx_id, op_domain, op_type,
                                                               op_before,
                                                               op_after, 'ok')
            except Exception as ex:
                raise
            return ret

        return _wrapper

    return _inner


def timer(func):
    @wraps(func)
    def _wrap(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        print(func.__name__, (end - start).total_seconds())
        return result

    return _wrap


def local_notify(func):
    @wraps(func)
    def _wrap(*args, **kwargs):
        if CONF.etc.env == 'local':
            print('\n______________________________')
            print(u'func: %s\n args: %s\n kwargs:\n %s' % (func.__name__, args, json.dumps(kwargs, indent=4)))
            print('\n______________________________\n')
            return
        return func(*args, **kwargs)

    return _wrap
