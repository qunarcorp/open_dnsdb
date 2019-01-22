# -*- coding: utf-8 -*-

import json

from .. import db


class ViewSwitchIpDetail(db.Model):
    __tablename__ = 'tb_view_switch_ip_detail'
    id = db.Column(db.Integer, primary_key=True)
    switch_id = db.Column(db.Integer, nullable=False)
    domain_name = db.Column(db.String(256), nullable=False, primary_key=True)
    before_enabled_server_rooms = db.Column(db.String(256), default='[]')
    isp = db.Column(db.String(256), primary_key=True)
    before_state = db.Column(db.String(32), default='disabled')
    after_state = db.Column(db.String(32), default='disabled')

    def __init__(self, switch_id, domain_name, before_enabled_server_rooms, isp, before_state, after_state):
        self.switch_id = switch_id
        self.domain_name = domain_name
        self.before_enabled_server_rooms = json.dumps(before_enabled_server_rooms)
        self.isp = isp
        self.before_state = before_state
        self.after_state = after_state
