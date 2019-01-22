# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class DnsHeader(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_dns_zone_header'

    zone_name = db.Column(db.String(50), primary_key=True)
    header_content = db.Column(db.Text, nullable=False)
