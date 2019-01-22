# -*- coding: utf-8 -*-

import json

import requests
from oslo.config import cfg
from requests.auth import HTTPBasicAuth

from .exception import DnsdbException

CONF = cfg.CONF


class Api(object):
    def __init__(self, root, username='', password='', headers=None,
                 resp_wrapper=lambda x, y: x):
        self.root = root
        self.auth = HTTPBasicAuth(username, password)
        self.content_type_form = {
            'Content-type': 'application/x-www-form-urlencoded'}
        self.content_type_json = {
            'Content-type': 'application/json'}
        self.headers = headers or {}
        self.resp_wrapper = resp_wrapper

    def _wrap_headers(self, headers, ctype='form'):
        _headers = {}
        _headers.update(self.headers)
        _headers.update(headers or {})
        content_type = 'application/x-www-form-urlencoded' if ctype == 'form' \
            else 'application/json'
        _headers.update({
            'Content-type': content_type
        })
        return _headers

    def _get(self, url, params=None, headers=None, ctype='form', **kwargs):
        url = '%s%s' % (self.root, url)
        headers = self._wrap_headers(headers, ctype=ctype)
        params = params if params else {}
        resp = requests.get(
            url, auth=self.auth, headers=headers, params=params, **kwargs)
        req = dict(url=url, headers=headers, params=params)
        req.update(kwargs)
        return self.resp_wrapper(resp, req)

    def _post(self, url, headers=None, data=None, params=None,
              ctype='form', **kwargs):
        url = '%s%s' % (self.root, url)
        headers = self._wrap_headers(headers, ctype=ctype)
        params = params if params else {}
        data = data if data else {}
        if ctype == 'json':
            data = json.dumps(data)
        resp = requests.post(
            url, auth=self.auth, headers=headers, params=params, data=data,
            verify=False, **kwargs)
        req = dict(
            url=url, headers=headers, params=params, data=data, verify=False)
        req.update(kwargs)
        return self.resp_wrapper(resp, req)

    def get_form(self, url, *args, **kwargs):
        return self._get(url, *args, **dict(kwargs, **{'ctype': 'form'}))

    def get_json(self, url, *args, **kwargs):
        return self._get(url, *args, **dict(kwargs, **{'ctype': 'json'}))

    def post_form(self, url, *args, **kwargs):
        return self._post(url, *args, **dict(kwargs, **{'ctype': 'form'}))

    def post_json(self, url, *args, **kwargs):
        return self._post(url, *args, **dict(kwargs, **{'ctype': 'json'}))


def _updater_resp_wrapper(resp, req):
    try:
        resp = resp.json()
    except Exception as ex:
        raise DnsdbException(
            u'DnsdbApi request error', 500, detail=dict(
                request=req, ex=str(ex), reason=resp.reason,
                status=resp.status_code),
            msg_ch=u'DnsUpdater调用失败')
    if int(resp.get('status', 200)) != 200 or resp.get('errcode', 0) != 0:
        raise DnsdbException(u'DnsUpdater调用失败', 400, json.dumps(resp))
    return resp


class DnsUpdaterApi(Api):
    def __init__(self, host_ip, username='', password='', headers=None):
        port = CONF.api.dnsupdater_port
        root = 'http://{}:{}/api'.format(host_ip, port)
        super(DnsUpdaterApi, self).__init__(root, username='', password='', headers=None,
                                            resp_wrapper=_updater_resp_wrapper)

    def notify_update_named(self, group_name, group_conf_md5):
        return self.post_json('/notify_update/named', data={
            'group_name': group_name,
            'group_conf_md5': group_conf_md5
        })

    def notify_update(self, deploy_type, group_name, **kwargs):
        return self.post_json('/notify_update',
                              data={
                                  'update_type': deploy_type,
                                  'group_name': group_name,
                                  'params': kwargs
                              })
