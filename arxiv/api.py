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


def pagination():
    page = max(1, int(flask.request.args.get("page", 1)))
    per_page = min(max(1, int(flask.request.args.get("per_page", 50))), 500)
    return page, per_page


@api.route("/search")
def search():
    q = flask.request.args.get("q")
    if q is None or not len(q.strip()):
        return flask.jsonify(message="You must include a search query"), 400

    # Pagination.
    page, per_page = pagination()

    tokens, modifiers = tokenize_query(q.lower())
    filters = []

    # Start by parsing any modifiers.
    # Extract the categories.
    if "category" in modifiers:
        categories = []
        for c in modifiers["category"]:
            categories += Category.query.filter(func.lower(Category.raw)
                                                .like("{0}%".format(c))).all()
        if not len(categories):
            return flask.jsonify(message="No categories matching query")
        filters.append(Abstract.categories.any(
            Category.id.in_([c.id for c in categories])))

    # Extract the authors.
    if "author" in modifiers:
        for a in modifiers["author"]:
            authors = Author.query.filter(func.lower(Author.lastname)
                                          .like("{0}%".format(a))).all()
            if not len(authors):
                return flask.jsonify(message="No match for author '{0}'"
                                             .format(a))
            filters.append(Abstract.authors.any(
                AuthorOrder.author_id.in_([au.id for au in authors])))

    # Perform the search.
    if len(tokens):
        abstracts = Abstract.query.filter(
            and_("abstracts.search_vector @@ plainto_tsquery(:terms)",
                 *filters))
        abstracts = abstracts.order_by("ts_rank_cd(abstracts.search_vector, "
                                       "plainto_tsquery(:terms)) DESC")
        abstracts = abstracts.params(terms=" ".join(tokens))

    else:
        abstracts = Abstract.query.filter(and_(*filters))
        abstracts = abstracts.order_by(Abstract.updated.desc())

    abstracts = abstracts.offset((page-1)*per_page).limit(per_page).all()

    return flask.jsonify(count=len(abstracts),
                         page=page, per_page=per_page,
                         results=[a.short_repr() for a in abstracts])


@api.route("/abs/<arxiv_id>")
def detail_view(arxiv_id):
    a = Abstract.query.filter(Abstract.arxiv_id == arxiv_id).first()
    if a is None:
        return flask.jsonify(message="No abstract found for ID '{0}'"
                                     .format(arxiv_id)), 404
    return flask.jsonify(result=a.full_repr())
