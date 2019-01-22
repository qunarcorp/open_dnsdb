# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


# named conf for host group
class DnsNamedConf(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_dns_named_conf'

    name = db.Column(db.String(64), primary_key=True)
    conf_content = db.Column(db.Text, nullable=False)
