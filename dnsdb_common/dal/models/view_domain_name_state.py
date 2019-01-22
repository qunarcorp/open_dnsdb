# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewDomainNameState(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_domain_name_state'

    domain_name = db.Column(db.String(256), nullable=False, primary_key=True)
    origin_enabled_rooms = db.Column(db.String(256), default="[]", nullable=False)
    origin_state = db.Column(db.String(32), default='disabled', nullable=False)
    enabled_rooms = db.Column(db.String(256), default="[]", nullable=False)
    isp = db.Column(db.String(256), primary_key=True)
    state = db.Column(db.String(32), default='disabled')
