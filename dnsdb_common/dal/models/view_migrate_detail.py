# -*- coding: utf-8 -*-

import json

from .. import db


# 记录每次迁移的详情
class ViewMigrateDetail(db.Model):
    __tablename__ = 'tb_view_migrate_detail'
    id = db.Column(db.Integer, primary_key=True)
    migrate_id = db.Column(db.Integer, nullable=False)
    domain_name = db.Column(db.String(256), nullable=False)
    before_enabled_server_rooms = db.Column(db.String(256), default='[]')
    after_enabled_server_rooms = db.Column(db.String(256), default='[]')
    isp = db.Column(db.String(256))
    before_state = db.Column(db.String(32), default='disabled')
    after_state = db.Column(db.String(32), default='disabled')

