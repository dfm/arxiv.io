#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask

from .api import run_query
from .models import Abstract

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    q = flask.request.args.get("q")
    if q is not None and len(q.strip()):
        return flask.render_template("searchbox.html",
                                     abstracts=run_query(q, 1, 50))
    return flask.render_template("searchbox.html")


@frontend.route("/abs/<arxiv_id>")
def abstract_view(arxiv_id):
    abstract = Abstract.query.filter(Abstract.arxiv_id == arxiv_id)
    abstract = abstract.order_by(Abstract.updated.desc()).first()
    if abstract is None:
        return flask.abort(404)
    return flask.render_template("searchbox.html", abstracts=[abstract])
