#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    return "Hello"
