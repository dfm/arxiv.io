#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    return flask.render_template("searchbox.html")


@frontend.route("/complete")
def complete():
    return flask.jsonify(values=[
        dict(value="DUDE", tokens=["DUDE"]),
    ])
