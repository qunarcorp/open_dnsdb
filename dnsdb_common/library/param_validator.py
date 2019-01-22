# -*- coding: utf-8 -*-

from flask import request
from .exception import BadParam

class QInvalidParamException(BadParam):
    pass


O_PARAM_OPTIONAL = True
O_PARAM_REQUIRED = False

_REQUEST_TYPES = (
    'GET',
    'POST'
)

_PARAM_TYPES_MAPPING = {
    'boolean': True,
    'int': 1,
    'float': 1.1,
    'str': '',
    'list': [],
    'tuple': (),
    'set': set(''),
    'dict': {}
}

_MINETYPES = (
    'form',
    'json'
)

_PARAM_META_AMOUNT = 6

_META_INDEX_PARAM_NAME = 0
_META_INDEX_PARAM_TYPE = 1
_META_INDEX_REQUEST_METHOD = 2
_META_INDEX_MIMETYPE = 3
_META_INDEX_IS_OPTIONAL = 4
_META_INDEX_DEFAULT_VALUE = 5


def ParamValidator(params_meta):
    params = {}
    _ValidParamsMeta(params_meta)
    _ParseParamsMeta(params_meta, params)
    _ValidParamsType(params_meta, params)
    return params


def _ValidParamsMeta(params_meta):
    unique_param_name = []
    for each_param in params_meta:
        if len(each_param) != _PARAM_META_AMOUNT:
            raise QInvalidParamException(
                u'ParamValidator meta info error: Invalid number of arguments. [%s]' % str(each_param))
        _ValidEachParamMeta(each_param)
        if each_param[_META_INDEX_PARAM_NAME] in unique_param_name:
            raise QInvalidParamException(
                u'ParamValidator meta info error: Repeat definition param name. [%s]' % str(each_param))
        else:
            unique_param_name.append(each_param[_META_INDEX_PARAM_NAME])


def _ValidEachParamMeta(param_meta):
    _ERROR_MSG_TEMPLATE = u'ParamValidator meta info error: %s. [%s]'

    if param_meta[_META_INDEX_PARAM_NAME] is None \
            or str(param_meta[_META_INDEX_PARAM_NAME]) == '':
        raise QInvalidParamException(_ERROR_MSG_TEMPLATE % (u'Invalid param name', str(param_meta)))
    if not isinstance(param_meta[_META_INDEX_PARAM_NAME], str):
        raise QInvalidParamException(
            _ERROR_MSG_TEMPLATE % (u'Invalid param name meta type: Require str', str(param_meta)))
    if param_meta[_META_INDEX_PARAM_TYPE] is None \
            or str(param_meta[_META_INDEX_PARAM_TYPE]).lower() not in _PARAM_TYPES_MAPPING:
        raise QInvalidParamException(_ERROR_MSG_TEMPLATE % (u'Invalid param type', str(param_meta)))
    if param_meta[_META_INDEX_REQUEST_METHOD] is None \
            or str(param_meta[_META_INDEX_REQUEST_METHOD]).upper() not in _REQUEST_TYPES:
        raise QInvalidParamException(_ERROR_MSG_TEMPLATE % (u'Invalid HTTP request method', str(param_meta)))
    if param_meta[_META_INDEX_MIMETYPE] is None \
            or str(param_meta[_META_INDEX_MIMETYPE]).lower() not in _MINETYPES:
        # 如果没有指定MineTypes则必须使用GET, 否则出错
        if str(param_meta[_META_INDEX_REQUEST_METHOD]).upper() != 'GET':
            raise QInvalidParamException(_ERROR_MSG_TEMPLATE % (u'Invalid HTTP Minetype', str(param_meta)))
    if not isinstance(param_meta[_META_INDEX_IS_OPTIONAL], bool):
        raise QInvalidParamException(_ERROR_MSG_TEMPLATE % (u'Invalid param optional flag meta type', str(param_meta)))


def _ParseParamsMeta(params_meta, result):
    for each_param in params_meta:
        _ParseEachParamMeta(each_param, result)


def _ParseEachParamMeta(param_meta, result):
    http_request_method = str(param_meta[_META_INDEX_REQUEST_METHOD]).upper()
    if http_request_method == 'GET':
        _ParseHttpGetParam(param_meta, result)
    elif http_request_method == 'POST':
        _ParseHttpPostParam(param_meta, result)
    else:
        raise QInvalidParamException(
            u'ParamValidator meta info error: Invalid HTTP request method. [%s]' % str(param_meta))


def _ParseHttpGetParam(param_meta, result):
    param_name = str(param_meta[_META_INDEX_PARAM_NAME])
    try:
        result[param_name] = request.args[param_name]
    except Exception:
        if param_meta[_META_INDEX_IS_OPTIONAL] == O_PARAM_OPTIONAL:
            result[param_name] = param_meta[_META_INDEX_DEFAULT_VALUE]
        else:
            raise QInvalidParamException(u'Missing Param: %s' % param_name)


def _ParseHttpPostParam(param_meta, result):
    param_name = str(param_meta[_META_INDEX_PARAM_NAME])
    try:
        mine_type = _ParseHttpMineType()
        if mine_type == 'form':
            result[param_name] = request.form[param_name]
        elif mine_type == 'json':
            result[param_name] = request.json[param_name]
        else:
            result[param_name] = request.form[param_name]
    except Exception:
        if param_meta[_META_INDEX_IS_OPTIONAL] == O_PARAM_OPTIONAL:
            result[param_name] = param_meta[_META_INDEX_DEFAULT_VALUE]
        else:
            raise QInvalidParamException(u'Missing Param: %s' % param_name)


def _ParseHttpMineType():
    mine_type = request.headers.get('Content-Type', '')
    if mine_type.lower() == u'':
        return ''
    elif mine_type.lower().startswith('application/json'):
        return 'json'
    elif mine_type.lower().startswith('application/x-www-form-urlencoded'):
        return 'form'
    else:
        raise QInvalidParamException(u'Invalid minetype: %s.' % str(mine_type))


def _ValidParamsType(params_meta, params):
    for each_param in params_meta:
        param_name = each_param[_META_INDEX_PARAM_NAME]
        param_type = each_param[_META_INDEX_PARAM_TYPE]
        try:
            _TryTypeCast(param_name, param_type, params)
        except Exception:
            raise QInvalidParamException(
                u'%s type is invalid: [Require: %s Actual: %s]' %
                (param_name, str(param_type),
                 str(type(params[param_name])).replace(
                     "<type '", '').replace("'>", '')))


def _TryTypeCast(param_name, param_type, params):
    if param_type == 'str':
        params[param_name] = _PARAM_TYPES_MAPPING[param_type].__class__(
            params[param_name].encode('utf-8'))
    else:
        params[param_name] = _PARAM_TYPES_MAPPING[param_type].__class__(
            params[param_name])
