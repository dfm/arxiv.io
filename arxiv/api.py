#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["api", "run_query"]

import flask

import string
from sqlalchemy import func, and_

from .qparser import tokenize_query
from .models import Author, AuthorOrder, Category, Abstract

api = flask.Blueprint("api", __name__)


def pagination():
    page = max(1, int(flask.request.args.get("page", 1)))
    per_page = min(max(1, int(flask.request.args.get("per_page", 50))), 500)
    return page, per_page


def author_search(nm):
    # Reorder in the case of a comma.
    nm = " ".join(nm.lower().split(",")[::-1])

    # Tokenize the name.
    tokens = [t.strip(string.punctuation) for t in nm.split()]
    if len(tokens) == 1:
        tokens = [""] + tokens

    # Re-order to make sure that the initials are at the front.
    search = "% ".join(tokens)
    sim = " ".join(tokens)

    # Do the search using the trigram index and sort by trigam similarity.
    q = Author.query.filter(func.lower(Author.fullname).like(search))
    q = q.order_by(func.similarity(func.lower(Author.fullname), sim))

    return q.all()


def run_query(q, page, per_page):
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
            flask.flash("No categories matching query")
            return []
        filters.append(Abstract.categories.any(
            Category.id.in_([c.id for c in categories])))

    # Extract the authors.
    if "author" in modifiers:
        for a in modifiers["author"]:
            authors = author_search(a)
            if not len(authors):
                flask.flash("No matches found for author '{0}'".format(a))
                return []
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

    # Apply the pagination.
    abstracts = abstracts.offset((page-1)*per_page).limit(per_page)
    return abstracts.all()


@api.route("/search")
def search():
    q = flask.request.args.get("q")
    if q is None or not len(q.strip()):
        return flask.jsonify(message="You must include a search query"), 400
    page, per_page = pagination()

    abstracts = run_query(q, page, per_page)

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
