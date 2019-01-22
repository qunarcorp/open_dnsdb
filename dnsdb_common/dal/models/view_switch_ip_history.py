# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


# 记录ip切换记录
class ViewSwitchIpHistory(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_switch_ip_history'
    id = db.Column(db.Integer, primary_key=True)
    switch_ip = db.Column(db.String(32), nullable=False)
    switch_type = db.Column(db.String(32), nullable=False)
    switch_to = db.Column(db.String(32), nullable=False)
    state = db.Column(db.String(32), default='switched')
    rtx_id = db.Column(db.String(256), nullable=False)

    def __init__(self, switch_ip, switch_type, switch_to, state, update_at, rtx_id):
        self.switch_ip = switch_ip
        self.switch_type = switch_type
        self.switch_to = switch_to
        self.state = state
        self.update_at = update_at
        self.rtx_id = rtx_id
