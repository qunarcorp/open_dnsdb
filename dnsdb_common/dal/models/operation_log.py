# -*- coding: utf-8 -*-

from .. import db
from . import JsonMixin


class OperationLog(db.Model, JsonMixin):
    __tablename__ = 'tb_operation_log'

    id = db.Column(db.Integer, primary_key=True)
    rtx_id = db.Column(db.String(256), nullable=False)
    op_domain = db.Column(db.String(256), nullable=False)
    op_type = db.Column(db.String(32), nullable=False)
    op_before = db.Column(db.String(2048), nullable=False)
    op_after = db.Column(db.String(2048), nullable=False)
    op_time = db.Column(db.DateTime, nullable=False)
    op_result = db.Column(db.String(32), nullable=False)
