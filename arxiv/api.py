#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["api"]

import flask

from sqlalchemy import func, and_

from .qparser import tokenize_query
from .models import Author, Category, Abstract

api = flask.Blueprint("api", __name__)


@api.route("/search")
def search():
    q = flask.request.args.get("q")
    if q is None:
        return flask.jsonify(message="You must include a search query"), 400

    tokens, modifiers = tokenize_query(q.lower())

    # Start by parsing any modifiers.
    # Extract the categories.
    categories = []
    if "category" in modifiers:
        for c in modifiers["category"]:
            categories += Category.query.filter(func.lower(Category.raw)
                                                .like("{0}%".format(c))).all()
        if not len(categories):
            return flask.jsonify(message="No categories matching query")

        categories = [c.id for c in categories]

    # Extract the authors.
    authors = []
    if "author" in modifiers:
        for a in modifiers["author"]:
            authors += Author.query.filter(func.lower(Author.lastname)
                                           .like("{0}%".format(a))).all()
        if not len(authors):
            return flask.jsonify(message="No authors matching query")

        authors = [a.id for a in authors]

    # Do the search.
    if not len(tokens):
        filters = []
        if len(categories):
            filters.append(
                Abstract.categories.any(Category.id.in_(categories)))
        if len(authors):
            filters.append(
                Abstract.authors.any(Author.id.in_(authors)))

        abstracts = Abstract.query.filter(
            and_(*filters)).order_by(Abstract.updated).limit(100).all()

        return flask.jsonify(count=len(abstracts),
                             results=[a.arxiv_id for a in abstracts])

    return flask.jsonify(tokens=tokens, modifiers=modifiers)
