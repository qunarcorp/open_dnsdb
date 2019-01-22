# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class DnsHost(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_dns_host'

    id = db.Column(db.Integer, primary_key=True)
    host_name = db.Column(db.String(100), unique=True, nullable=False)
    host_group = db.Column(db.String(32), nullable=False)
    host_ip = db.Column(db.String(32), nullable=False)
    host_conf_md5 = db.Column(db.String(100))
