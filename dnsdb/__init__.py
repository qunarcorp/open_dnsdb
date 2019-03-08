# -*- coding: utf-8 -*-

import os
import sys

from flask import Flask
from flask_login import LoginManager
from flask_restful import abort
from oslo_config import cfg

from dnsdb.config import Config, setup_config
from dnsdb_common.dal import db
from dnsdb_common.library.log import getLogger
from dnsdb_common.library.gunicorn_app import GunicornApplication, number_of_workers
from dnsdb_common.library.utils import make_tmp_dir
from dnsdb_common.library.log import setup

CONF = cfg.CONF

setup('dnsdb')
LOG = getLogger(__name__)

def get_flask_app():
    app = Flask(__name__)
    app.config.from_object(CONF.flask_conf)
    db.init_app(app)
    return app


def init_login_manager():
    login_manager = LoginManager()
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'

    from dnsdb_common.dal.models.user import User, AnonymousUser
    login_manager.anonymous_user = AnonymousUser

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return login_manager


def createApp(app_env, app_kind, conf_dir):
    app = Flask(__name__)
    config_obj = Config(app_env, app_kind, conf_dir)
    CONF.flask_conf = config_obj
    app.config.from_object(config_obj)

    CONF.tmp_dir = make_tmp_dir('./tmp')

    db.init_app(app)
    login_manager = init_login_manager()
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return abort(401)

    LOG.info("dnsdb.started")

    @app.context_processor
    def default_context_processor():
        result = {'config': {'BASE_URL': CONF.web.base_url}}
        return result

    from dnsdb.view.web import root
    app.register_blueprint(root.bp, url_prefix='/')

    from dnsdb.view.web import auth
    app.register_blueprint(auth.bp, url_prefix='/web/auth')

    from dnsdb.view.web import user
    app.register_blueprint(user.bp, url_prefix='/web/user')

    from dnsdb.view.web import preview
    app.register_blueprint(preview.bp, url_prefix='/web/preview')

    from dnsdb.view.web import config
    app.register_blueprint(config.bp, url_prefix='/web/config')

    from dnsdb.view.web import subnet
    app.register_blueprint(subnet.bp, url_prefix='/web/subnet')

    from dnsdb.view.web import record
    app.register_blueprint(record.bp, url_prefix='/web/record')

    from dnsdb.view.web import view_isp
    app.register_blueprint(view_isp.bp, url_prefix='/web/view')

    from dnsdb.view.web import view_record
    app.register_blueprint(view_record.bp, url_prefix='/web/view')

    from dnsdb.view import api
    app.register_blueprint(api.bp, url_prefix='/api')

    return app


def main():
    application = createApp(sys.argv[1], sys.argv[2], conf_dir=os.path.dirname(os.path.dirname(__file__)))
    options = {
        'workers': number_of_workers(),
    }
    for option in CONF.gunicorn:
        options[option] = CONF.gunicorn[option]

    GunicornApplication(application, options).run()


if __name__ == '__main__':
    application = createApp(app_env='dev', app_kind='dnsdb', conf_dir=os.path.dirname(os.path.abspath('.')))
    application.run(host='0.0.0.0', port=8888, debug=True)
