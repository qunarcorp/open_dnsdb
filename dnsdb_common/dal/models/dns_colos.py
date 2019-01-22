# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class DnsColo(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_colo_config'

    id = db.Column(db.Integer)
    colo_name = db.Column(db.String(64), primary_key=True)
    colo_group = db.Column(db.String(64), primary_key=True)
    create_user = db.Column(db.String(64), nullable=False)
