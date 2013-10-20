#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = []

import nltk
import flask
import string

stopwords = None


def get_bag_of_words(textblock):
    # Load the stop words on the first pass.
    global stopwords
    if stopwords is None:
        with flask.current_app.open_resource("stopwords.txt") as f:
            stopwords = [w.strip() for w in f]

    # Tokenize the document.
    tokens = [t for t in nltk.word_tokenize(textblock.lower())
              if t not in stopwords]

    # Stem the tokens and strip punctuation from the ends of the words.
    stemmer = nltk.PorterStemmer()
    return [t for t in [stemmer.stem(t.strip(string.punctuation))
                        for t in tokens
                        if t not in string.punctuation]
            if len(t)]
