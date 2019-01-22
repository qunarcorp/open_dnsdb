# -*- coding: utf-8 -*-

from . import AuditTimeMixin, JsonMixin
from .. import db


class ViewIsps(db.Model, AuditTimeMixin, JsonMixin):
    __tablename__ = 'tb_view_isps'

    name_in_english = db.Column(db.String(64), primary_key=True)
    abbreviation = db.Column(db.String(32), unique=True, nullable=False)
    name_in_chinese = db.Column(db.String(64), unique=True, nullable=False)
    acl_name = db.Column(db.String(64), unique=True)
    acl_file = db.Column(db.String(64))
    username = db.Column(db.String(64), nullable=False)
