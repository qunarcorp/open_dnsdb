# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class DnsHostGroup(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_dns_host_group'

    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(32), unique=True, nullable=False)
    group_type = db.Column(db.String(32), nullable=False)
    # 组配置md5 和线上配置定时对比
    group_conf_md5 = db.Column(db.String(100))
    reload_status = db.Column(db.Boolean, default=True)
