# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewConfigs(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_configs'

    key = db.Column(db.String(256), nullable=False, primary_key=True)
    value = db.Column(db.String(256), default='')
