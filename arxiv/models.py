#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["Abstract", "Author", "Category", "User", "Click", "Like",
           "Dislike"]

import os
from hashlib import sha1
from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime,
                        ForeignKey, Table)
from sqlalchemy.orm import relationship

from .database import db
from .nlp import get_bag_of_words
from .email_utils import hash_email, encrypt_email, decrypt_email


publications = Table("publications", db.Model.metadata,
                     Column("author_id", Integer, ForeignKey("authors.id")),
                     Column("abstract_id", Integer,
                            ForeignKey("abstracts.id")))

categories = Table("abstract_categories", db.Model.metadata,
                   Column("category_id", Integer, ForeignKey("categories.id")),
                   Column("abstract_id", Integer, ForeignKey("abstracts.id")))


class Abstract(db.Model):

    __tablename__ = "abstracts"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String)
    title = Column(String)
    abstract = Column(String)
    date = Column(DateTime)
    license = Column(String)
    wordbag = Column(String)
    authors = relationship("Author", secondary=publications,
                           backref="abstracts")
    categories = relationship("Category", secondary=categories,
                              backref="abstracts")

    def __init__(self, arxiv_id, title, abstract, date_str, license,
                 author_list, category_str):
        self.arxiv_id = arxiv_id
        self.title = title
        self.abstract = abstract
        self.date_str = datetime.strptime(date_str, "%Y-%m-%d")
        self.license = license

        # Upsert the authors into the database.
        self.authors = []
        for fn, ln in author_list:
            fn, ln = fn.strip(), ln.strip()
            author = Author.query.filter_by(firstname=fn,
                                            lastname=ln).first()
            if author is None:
                author = Author(fn, ln)
            self.authors.append(author)

        # Parse and upsert the categories into the database.
        self.categories = []
        for c in category_str.split():
            c = c.strip()
            category = Category.query.filter_by(raw=c).first()
            if category is None:
                category = Category(c)
            self.categories.append(category)

        # Compute the bag-of-words representation of this abstract.
        self.wordbag = " ".join(get_bag_of_words(title + " " + abstract))

    def __repr__(self):
        return "Abstract(\"{0}\", ...)".format(self.arxiv_id)


class Author(db.Model):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)

    def __init__(self, fn, ln):
        self.firstname = fn
        self.lastname = ln

    def __repr__(self):
        return "Author(\"{0}\", \"{1}\")".format(self.firstname,
                                                 self.lastname)


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


class User(db.Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String)
    email = Column(String)
    email_hash = Column(String)
    refresh_token = Column(String)
    joined = Column(DateTime)

    def __init__(self, email, refresh_token, joined=None):
        self.email = encrypt_email(email)
        self.email_hash = hash_email(email)
        self.refresh_token = refresh_token
        self.joined = joined if joined is not None else datetime.now()

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
