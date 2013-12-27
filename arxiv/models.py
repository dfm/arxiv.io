#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["Abstract", "Author", "Category", "User", "Click", "Like",
           "Dislike"]

import os
import bleach
import logging
import markdown
from hashlib import sha1
from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime,
                        ForeignKey, Table)
from sqlalchemy.orm import relationship

from .database import db
from .email_utils import hash_email, encrypt_email, decrypt_email


categories = Table("abstract_categories", db.Model.metadata,
                   Column("category_id", Integer, ForeignKey("categories.id")),
                   Column("abstract_id", Integer, ForeignKey("abstracts.id")))


class AuthorOrder(db.Model):

    __tablename__ = "author_order"

    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)
    abstract_id = Column(Integer, ForeignKey("abstracts.id"), primary_key=True)
    order = Column(Integer, primary_key=True)
    author = relationship("Author")

    def __init__(self, author, order):
        self.author = author
        self.order = order

    def short_repr(self):
        return self.author.short_repr()

    def full_repr(self):
        return self.author.full_repr()


class Abstract(db.Model):

    __tablename__ = "abstracts"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String)
    title = Column(String)
    abstract = Column(String)
    created = Column(DateTime)
    updated = Column(DateTime)
    license = Column(String)
    authors = relationship(AuthorOrder, lazy="join")
    categories = relationship("Category", secondary=categories,
                              backref="abstracts", lazy="join")

    def __init__(self, arxiv_id, title, abstract, created_str, updated_str,
                 license, author_list, category_str):
        self.arxiv_id = arxiv_id
        self.title = title
        self.abstract = abstract
        self.created = datetime.strptime(created_str, "%Y-%m-%d")
        if updated_str is not None:
            self.updated = datetime.strptime(updated_str, "%Y-%m-%d")
        self.license = license

        # Parse and upsert the categories into the database.
        self.categories = []
        for c in category_str.split():
            c = c.strip()
            category = Category.query.filter_by(raw=c).first()
            if category is not None:
                self.categories.append(category)
            else:
                logging.warn("Missing category: '{0}'".format(c))

        self.authors = []
        for i, (fn, ln) in enumerate(author_list):
            # Upsert the author.
            author = Author.query.filter_by(firstname=fn,
                                            lastname=ln).first()
            if author is None:
                author = Author(fn, ln)

            # Upsert the author order entry.
            order = AuthorOrder(author, i)
            self.authors.append(order)

    def __repr__(self):
        return "Abstract(\"{0}\", ...)".format(self.arxiv_id)

    def short_repr(self):
        return dict(
            id=self.arxiv_id,
            title=bleach.clean(self.title),
            date=self.updated.strftime("%Y-%m-%d"),
            categories=[c.short_repr() for c in self.categories],
            authors=[a.short_repr() for a in sorted(self.authors,
                                                    key=lambda a: a.order)],
        )

    def full_repr(self):
        return dict(
            id=self.arxiv_id,
            title=bleach.clean(self.title),
            abstract=markdown.markdown(self.abstract),
            date=self.updated.strftime("%Y-%m-%d"),
            categories=[c.full_repr() for c in self.categories],
            authors=[a.full_repr() for a in sorted(self.authors,
                                                   key=lambda a: a.order)],
        )


# Full text search in abstracts table.
def abstracts_search_setup(event, schema_item, bind):
    bind.execute("alter table abstracts add column search_vector tsvector")
    bind.execute("""create index abstracts_search_index on abstracts
                    using gin(search_vector)""")
    bind.execute("""create trigger abstracts_search_update before update or
                    insert on abstracts
                    for each row execute procedure
                    tsvector_update_trigger('search_vector',
                                            'pg_catalog.english',
                                            'abstract',
                                            'title')""")

    # Completion indexes.
    bind.execute("""CREATE INDEX abstract_arxiv_id_pre ON abstracts
                    USING btree ( lower (arxiv_id) text_pattern_ops)""")


Abstract.__table__.append_ddl_listener("after-create", abstracts_search_setup)


class Author(db.Model):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    firstname = Column(String)
    lastname = Column(String)

    def __init__(self, fn, ln):
        self.fullname = ((fn + " " if fn is not None else "")
                         + (ln if ln is not None else ""))
        self.firstname = fn
        self.lastname = ln

    def __repr__(self):
        return "Author(\"{0}\", \"{1}\")".format(self.firstname,
                                                 self.lastname)

    def short_repr(self):
        return self.fullname

    def full_repr(self):
        return [n for n in [self.firstname, self.lastname] if n is not None]


# Full text search in authors table.
def authors_search_setup(event, schema_item, bind):
    bind.execute("""CREATE INDEX author_firstname_pre ON authors USING btree
                    ( lower (firstname) text_pattern_ops)""")
    bind.execute("""CREATE INDEX author_lastname_pre ON authors USING btree
                    ( lower (lastname) text_pattern_ops)""")


Author.__table__.append_ddl_listener("after-create", authors_search_setup)


class Category(db.Model):

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    raw = Column(String)
    category = Column(String)
    subcategory = Column(String)

    def __init__(self, rawstring):
        parts = rawstring.split(".")
        self.raw = rawstring
        self.category = parts[0]
        if len(parts) > 1:
            self.subcategory = parts[1]

    def __repr__(self):
        return "Category(\"{0}\")".format(self.raw)

    def short_repr(self):
        return self.raw

    def full_repr(self):
        return self.raw


# Full text search in abstracts table.
def category_search_setup(event, schema_item, bind):
    bind.execute("""CREATE INDEX category_pre ON categories
                    USING btree ( lower (raw) text_pattern_ops)""")


Category.__table__.append_ddl_listener("after-create", category_search_setup)


class User(db.Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    email_hash = Column(String)
    refresh_token = Column(String)
    joined = Column(DateTime)
    api_key = Column(String)

    def __init__(self, email, refresh_token, joined=None):
        self.email = encrypt_email(email)
        self.email_hash = hash_email(email)
        self.refresh_token = refresh_token
        self.joined = joined if joined is not None else datetime.now()
        self.api_key = self.generate_token()

    def get_email(self):
        return decrypt_email(self.email)

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def generate_token(self):
        return sha1(os.urandom(8)+self.get_email()+os.urandom(8)).hexdigest()


class Click(db.Model):

    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    user = relationship("User", backref="clicks")
    user_id = Column(Integer, ForeignKey("users.id"))
    abstract = relationship("Abstract")
    abstract_id = Column(Integer, ForeignKey("abstracts.id"))

    def __init__(self, user, abstract, date=None):
        if date is None:
            date = datetime.now()
        self.user = user
        self.abstract = abstract

    def __repr__(self):
        return "Click({0}, {1}, date={2})".format(map(repr, [self.user,
                                                             self.abstract,
                                                             self.date]))


class Like(db.Model):

    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    user = relationship("User", backref="likes")
    user_id = Column(Integer, ForeignKey("users.id"))
    abstract = relationship("Abstract")
    abstract_id = Column(Integer, ForeignKey("abstracts.id"))

    def __init__(self, user, abstract, date=None):
        if date is None:
            date = datetime.now()
        self.user = user
        self.abstract = abstract

    def __repr__(self):
        return "Like({0}, {1}, date={2})".format(map(repr, [self.user,
                                                            self.abstract,
                                                            self.date]))


class Dislike(db.Model):

    __tablename__ = "dislikes"

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    user = relationship("User", backref="dislikes")
    user_id = Column(Integer, ForeignKey("users.id"))
    abstract = relationship("Abstract")
    abstract_id = Column(Integer, ForeignKey("abstracts.id"))

    def __init__(self, user, abstract, date=None):
        if date is None:
            date = datetime.now()
        self.user = user
        self.abstract = abstract

    def __repr__(self):
        return "Dislike({0}, {1}, date={2})".format(map(repr, [self.user,
                                                               self.abstract,
                                                               self.date]))
