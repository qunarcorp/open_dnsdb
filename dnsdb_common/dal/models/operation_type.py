# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class OperationType(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_operation_type'

    id = db.Column(db.Integer, primary_key=True)
    op_type = db.Column(db.String(64), unique=True, nullable=False)
    op_chinese = db.Column(db.String(128), unique=True, nullable=False)
    # logs = db.relationship('User', backref='role', lazy='dynamic')
