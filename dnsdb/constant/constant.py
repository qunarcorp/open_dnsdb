# -*- coding: utf-8 -*-

from oslo.config import cfg
CONF = cfg.CONF

RE_PATTERN = {
    'username': r'(^[\w\.]{1-64}$)',
    'email': r'^([\w-_]+(?:\.[\w-_]+)*)@((?:[a-z0-9]+(?:-[a-zA-Z0-9]+)*)+\.[a-z]{2,6})$',
    'password': r'^(?=[\s\S]{6,9}$)(?=[\s\S]*[A-Z])(?=[\s\S]*[a-z])(?=[\s\S]*[0-9]).*'
}

NORMAL_TO_CNAME = CONF.view.normal_cname
NORMAL_TO_VIEW = CONF.view.normal_view
VIEW_ZONE = CONF.view.view_zone
