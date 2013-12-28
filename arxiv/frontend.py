#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask

from .api import run_query

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    q = flask.request.args.get("q")
    if q is not None and len(q.strip()):
        return flask.render_template("searchbox.html",
                                     abstracts=run_query(q, 1, 50))
    return flask.render_template("searchbox.html")
