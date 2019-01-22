# -*- coding: utf-8 -*-

from . import AuditTimeMixin
from .. import db


class DeployHistory(db.Model, AuditTimeMixin):
    __tablename__ = 'tb_deploy_history'

    id = db.Column(db.Integer, primary_key=True)
    rtx_id = db.Column(db.String(50), nullable=False)
    deploy_desc = db.Column(db.Text, nullable=False)
    state = db.Column(db.String(50), nullable=False)
