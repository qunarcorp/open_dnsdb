# -*- coding: utf-8 -*-

from .. import db


class OperationLogDetail(db.Model):
    __tablename__ = 'tb_operation_log_detail'

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, nullable=False)
    detail = db.Column(db.String(1024), default='')
