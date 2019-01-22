# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class Subnets(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_subnets'

    id = db.Column(db.Integer, primary_key=True)
    region_name = db.Column(db.String(80), nullable=False, unique=True)
    subnet = db.Column(db.String(50), nullable=False)
    create_user = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.String(100))
    colo = db.Column(db.String(64), nullable=False, default='')
    intranet = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<Subnets> [region_name: %s, subnet: %s]' % (self.region_name, self.subnet)
