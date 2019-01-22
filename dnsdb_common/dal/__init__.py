# -*- coding: utf-8 -*-

from functools import wraps

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={
    'autocommit': True
})


def commit_on_success(func):
    @wraps(func)
    def decorator(*kargs, **kwargs):
        with db.session.begin(subtransactions=True):
            return func(*kargs, **kwargs)

    return decorator
