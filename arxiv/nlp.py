#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = []

import nltk
from nltk.corpus import stopwords


def get_bag_of_words(textblock):
    tokens = nltk.word_tokenize(textblock)
    stemmer = nltk.PorterStemmer()
    stop = stopwords.words("english")
    return [stemmer.stem(t) for t in tokens if t not in stop]
