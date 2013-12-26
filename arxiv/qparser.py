#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["tokenize_query"]

import re
from collections import defaultdict

prefixes = ["author", "category", "from", "to"]
synonyms = {
    "au": "author",
    "cat": "category",
    "since": "from",
    "until": "to",
}
all_prefixes = prefixes + synonyms.keys()
prefix_text = (r"(?:\b({0}):((?:"
               r"(?:\"(?:.+?)\")|"
               r"(?:'(?:.+?)')|"
               r"(?:(?:(?:.+?)(?:\s|$)))"
               r")))|"
               r"(\b(?:.+?)(?:\s|$))")
prefix_finder = re.compile(prefix_text.format("|".join(map("(?:{0})".format,
                                                           all_prefixes))),
                           re.I)


def tokenize_query(q):
    tokens = prefix_finder.findall(q)
    query = []
    modifiers = defaultdict(list)
    for token in tokens:
        if len(token[0]):
            k = token[0].lower()
            modifiers[synonyms.get(k, k)].append(token[1].strip())
        else:
            query.append(token[2].strip())
    return query, dict(modifiers)


if __name__ == "__main__":
    print(tokenize_query("emcee MCMC cat:astro-ph.IM since:2010 author:hogg"))
