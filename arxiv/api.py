#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["api"]

import flask

from sqlalchemy import func, and_

from .qparser import tokenize_query
from .models import Author, AuthorOrder, Category, Abstract

api = flask.Blueprint("api", __name__)


@api.route("/search")
def search():
    q = flask.request.args.get("q")
    if q is None or not len(q.strip()):
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
            return flask.jsonify(message="No authors matching query",
                                 authors=modifiers["author"])

        authors = [a.id for a in authors]

    filters = []
    if len(categories):
        filters.append(
            Abstract.categories.any(Category.id.in_(categories)))
    if len(authors):
        filters.append(
            Abstract.authors.any(AuthorOrder.author_id.in_(authors)))

    if len(tokens):
        abstracts = Abstract.query.filter(
            and_("abstracts.search_vector @@ plainto_tsquery(:terms)",
                 *filters))
        abstracts = abstracts.order_by("ts_rank_cd(abstracts.search_vector, "
                                       "plainto_tsquery(:terms)) DESC")
        abstracts = abstracts.params(terms=" ".join(tokens))

    else:
        abstracts = Abstract.query.filter(
            and_(*filters))
        abstracts = abstracts.order_by(Abstract.updated.desc())

    abstracts = abstracts.limit(100).all()

    return flask.jsonify(count=len(abstracts),
                         results=[a.short_repr() for a in abstracts])


@api.route("/abs/<arxiv_id>")
def detail_view(arxiv_id):
    a = Abstract.query.filter(Abstract.arxiv_id == arxiv_id).first()
    if a is None:
        return flask.jsonify(message="No abstract found for ID '{0}'"
                                     .format(arxiv_id)), 404
    return flask.jsonify(result=a.full_repr())
