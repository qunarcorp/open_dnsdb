# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class ViewAclCityCode(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_view_acl_city_code'
    code = db.Column(db.String(64), primary_key=True)
    country = db.Column(db.String(64), nullable=False)
    province = db.Column(db.String(64), nullable=False)
    city = db.Column(db.String(64))

    def __repr__(self):
        return 'ViewAclCityCode [code={}, province={}]'.format(
            self.code,
            self.province
        )
