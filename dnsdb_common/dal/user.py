# -*- coding: utf-8 -*-

from . import commit_on_success, db
from .models import User, Role
from ..library.exception import BadParam


class UserDal(object):
    ALLOWED_ROLES = [u'owner', u'dev']

    def __init__(self):
        pass

    @staticmethod
    def get_roles():
        return {item.id: item.name_ch for item in Role.query.all()}

    @staticmethod
    def get_role_name(role_id):
        role = Role.query.get(role_id)
        if role:
            return role.name
        else:
            return None

    @staticmethod
    def get_user_info(**kwargs):
        return User.query.filter_by(**kwargs).first()

    @staticmethod
    @commit_on_success
    def add_user(username, email, password, role_id):
        if User.query.filter_by(username=username).first():
            raise BadParam('user with username %s already exist.' % username)
        if User.query.filter_by(email=email).first():
            raise BadParam('user with email %s already exist.' % email)
        user = User(username=username, email=email, password=password, role_id=role_id)
        db.session.add(user)

    @staticmethod
    def list_user(role_id='', page=1, page_size=10):
        query = User.query
        if role_id:
            query = query.filter_by(role_id=role_id)
        # if page <= 0:
        #     page = 1
        return [obj.json_serialize() for obj in (query.
                                                 offset((page - 1) * page_size).
                                                 limit(page_size).all())]

    # @staticmethod
    # def reset_password(token, new_password):
    #     s = Serializer(current_app.config['SECRET_KEY'])
    #     try:
    #         data = s.loads(token.encode('utf-8'))
    #     except:
    #         return False
    #     user = User.query.get(data.get('reset'))
    #     if user is None:
    #         return False
    #     user.password = new_password
    #     db.session.add(user)
    #     return True

    @staticmethod
    @commit_on_success
    def delete_user(username):
        User.query.filter_by(username=username).delete()
