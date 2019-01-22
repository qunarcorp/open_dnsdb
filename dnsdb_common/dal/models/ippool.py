# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class IpPool(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_ippool'

    id = db.Column(db.Integer)
    fixed_ip = db.Column(db.String(256), primary_key=True)
    region = db.Column(db.String(50), nullable=False)
    allocated = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return '<IpPool> [fixed_ip: %s, region: %s]' % (self.ip, self.region)
