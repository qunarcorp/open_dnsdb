# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


# 记录迁移进度
class ViewMigrateHistory(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_view_migrate_history'

    id = db.Column(db.Integer, primary_key=True)
    migrate_rooms = db.Column(db.String(256), nullable=False)
    migrate_isps = db.Column(db.String(256), nullable=False)
    dst_rooms = db.Column(db.String(256), nullable=False)
    migrate_info = db.Column(db.Text)
    # 迁移规则: 'migrating', 'migrated', 'error', 'recovered'
    state = db.Column(db.String(32), default='migrating')
    cur = db.Column(db.Integer, nullable=False)
    all = db.Column(db.Integer, nullable=False)
    rtx_id = db.Column(db.String(256), nullable=False)

    # 不能并发的状态
    check_states = ('recovering', 'migrating')

    def __init__(self, migrate_rooms, migrate_isps, dst_rooms, state, cur, all, rtx_id):
        self.migrate_rooms = migrate_rooms
        self.migrate_isps = migrate_isps
        self.dst_rooms = dst_rooms
        self.state = state
        self.cur = cur
        self.all = all
        self.rtx_id = rtx_id

    def update(self, migrate_rooms, migrate_isps, dst_rooms, state, cur, all, rtx_id):
        self.migrate_rooms = migrate_rooms
        self.migrate_isps = migrate_isps
        self.dst_rooms = dst_rooms
        self.state = state
        self.cur = cur
        self.all = all
        self.rtx_id = rtx_id
