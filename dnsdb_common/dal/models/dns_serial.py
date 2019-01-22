# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class DnsSerial(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_dns_zone_serial'

    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(50), unique=True, nullable=False)
    zone_group = db.Column(db.String(64), nullable=False)
    serial_num = db.Column(db.BigInteger, nullable=False)
    update_serial_num = db.Column(db.BigInteger, nullable=False)
