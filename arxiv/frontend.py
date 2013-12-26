#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

import json
from sqlalchemy import func

from .models import Author, Category

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    return flask.render_template("searchbox.html")


@frontend.route("/complete")
def complete():
    q = flask.request.args.get("q").lower()

    categories = Category.query.filter(func.lower(Category.raw)
                                       .like("{0}%".format(q))).all()

    authors = Author.query.filter(func.lower(Author.lastname)
                                  .like("{0}%".format(q))).all()

    return json.dumps(
        [c.raw for c in categories] +
        [a.fullname for a in authors]
    )
