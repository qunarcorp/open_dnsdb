# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewIspStatus(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_isps_status'

    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer)
    recover_id = db.Column(db.Integer)
    room = db.Column(db.String(64), nullable=False)
    # chinanet, cmnet, unicom
    isp = db.Column(db.String(64), nullable=False)
    is_health = db.Column(db.Boolean, default=False, nullable=False)
    closed = db.Column(db.Boolean, default=False, nullable=False)
    update_user = db.Column(db.String(64), nullable=False)
