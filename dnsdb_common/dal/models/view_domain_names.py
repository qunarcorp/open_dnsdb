# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewDomainNames(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_domain_name'

    domain_name = db.Column(db.String(256), primary_key=True)
    cname = db.Column(db.String(256), nullable=False)
