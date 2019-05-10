# -*- coding: utf-8 -*-

import os
import sys

from flask import (Flask, render_template)
from flask_restful import abort
from jinja2 import TemplateNotFound
from oslo_config import cfg

from dns_updater.config import setup_config
from dnsdb_common.library.gunicorn_app import GunicornApplication, number_of_workers
from dnsdb_common.library.log import getLogger, setup

CONF = cfg.CONF
setup('dnsdb_updater_www')
log = getLogger(__name__)


def create_app():
    setup_config(sys.argv[1], 'dnsdb-updater', conf_dir=os.path.dirname(os.path.dirname(__file__)))
    log.error('This host belong to host group %s' % CONF.host_group)

    app = Flask(__name__)
    app.config['SECRET_KEY'] = CONF.etc.secret_key

    from dns_updater.utils.updater_util import check_necessary_options
    check_necessary_options()

    @app.route("/healthcheck.html", methods=['GET'])
    def health_check():
        try:
            return render_template('healthcheck.html')
        except TemplateNotFound:
            abort(404)

    @app.context_processor
    def default_context_processor():
        result = {'config': {'BASE_URL': CONF.web.base_url}}
        return result

    from dns_updater import api
    app.register_blueprint(api.bp, url_prefix='/api')

    return app


application = create_app()


def app_start():
    options = {
        'workers': number_of_workers(),
    }
    for option in CONF.gunicorn:
        options[option] = CONF.gunicorn[option]

    GunicornApplication(application, options).run()


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=9000, debug=True)
