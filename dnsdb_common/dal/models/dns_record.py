# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class DnsRecord(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_dns_record'

    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(512), nullable=False)
    record = db.Column(db.String(512), nullable=False)
    zone_name = db.Column(db.String(20), nullable=False)
    update_user = db.Column(db.String(50), nullable=False)
    record_type = db.Column(db.String(20), nullable=False)
    ttl = db.Column(db.Integer, nullable=False, default=0)
    onoff = db.Column(db.Boolean, nullable=False, default=True)
