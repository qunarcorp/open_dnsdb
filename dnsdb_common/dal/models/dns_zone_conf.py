# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class DnsZoneConf(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_dns_named_zone'

    zone_name = db.Column(db.String(50), primary_key=True)
    # zone在不同group上的配置
    zone_conf = db.Column(db.Text, nullable=False)
    zone_group = db.Column(db.String(64), primary_key=True)
    # 0 反解
    # 1 机房
    # 2 普通
    zone_type = db.Column(db.Integer, nullable=False)
