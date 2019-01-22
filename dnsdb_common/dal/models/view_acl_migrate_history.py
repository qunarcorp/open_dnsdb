# -*- coding: utf-8 -*-

from sqlalchemy.orm import relationship

from .. import db


class ViewAclMigrateHistory(db.Model):
    __tablename__ = 'tb_view_acl_migrate_history'
    id = db.Column(db.Integer, primary_key=True)
    subnet_id = db.Column(db.Integer, db.ForeignKey('tb_view_acl_subnets.id'))
    from_acl = db.Column(db.String(32))
    to_acl = db.Column(db.String(32), nullable=False)
    origin_acl = db.Column(db.String(32), nullable=False)
    create_user = db.Column(db.String(64), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    # 'migrated', 'recovered', 'remigrated'
    status = db.Column(db.String(32), default='migrated')
    reloaded = db.Column(db.Boolean, nullable=False, default=False)
    subnet = relationship("ViewAclSubnet")

    def __str__(self):
        return 'ViewAclSubnet[subnet=%s, from_isp=%s, to_isp=%s]' % (
            self.subnet_id,
            self.from_view,
            self.to_view
        )
