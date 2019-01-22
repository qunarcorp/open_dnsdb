# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewRecords(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_record'

    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(256), nullable=False)
    record = db.Column(db.String(256), nullable=False)
    record_type = db.Column(db.String(32), nullable=False)
    ttl = db.Column(db.Integer, nullable=False, default=60)
    property = db.Column(db.String(256), default='none')
    zone_name = db.Column(db.String(50), nullable=False)
