# -*- coding: utf-8 -*-


from flask import (abort, Blueprint)
from flask import render_template, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound

bp = Blueprint('root', 'root')


@bp.route("/", methods=['GET'])
@bp.route("/dnsdb/", methods=['GET'])
@bp.route("/api/", methods=['GET'])
def root(path=''):
    try:
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)


@bp.route("/index", methods=['GET'])
@login_required
def index(path=''):
    try:
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)


@bp.route("/healthcheck.html", methods=['GET'])
def health_check():
    try:
        return render_template('healthcheck.html')
    except TemplateNotFound:
        abort(404)
