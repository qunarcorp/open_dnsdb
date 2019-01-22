# -*- coding: utf-8 -*-

from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from . import AuditTimeMixin, JsonMixin
from .. import db


class Permission(object):
    GET = 1
    POST = 2
    ADMIN = 4


class Role(db.Model, JsonMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    name_ch = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            # 'User': ([Permission.GET], u'普通用户'),
            'Operator': ([Permission.GET, Permission.POST], u'管理员'),
            'Administrator': ([Permission.GET, Permission.POST, Permission.ADMIN], u'超级管理员')
        }
        default_role = 'Admin'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r][0]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            role.name_ch = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model, UserMixin, AuditTimeMixin, JsonMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.role = Role.query.get(self.role_id)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()
            self.role_id = self.role.id

    def json_serialize(self, include=('username', 'email', 'role_id'), exclude=None):
        data = super(User, self).json_serialize(include=include, exclude=exclude)
        if 'role' in include:
            data['role'] = self.role.name
        return data

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_user(self):
        return self.can(Permission.GET)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.update_time = datetime.utcnow()
        db.session.add(self)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False
