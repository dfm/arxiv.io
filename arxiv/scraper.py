#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility to download the metadata for every paper on the arXiv.

"""

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["download"]

import re
import time
import logging
import requests
import xml.etree.cElementTree as ET

from .database import db
from .models import Abstract

# Download constants
resume_re = re.compile(r".*<resumptionToken.*?>(.*?)</resumptionToken>.*")
url = "http://export.arxiv.org/oai2"

# Parse constant
record_tag = ".//{http://www.openarchives.org/OAI/2.0/}record"
format_tag = lambda t: ".//{http://arxiv.org/OAI/arXiv/}" + t
date_fmt = "%a, %d %b %Y %H:%M:%S %Z"


class NullElement:
    text = ""


def download(start_date, max_tries=10):
    params = {"verb": "ListRecords", "metadataPrefix": "arXiv",
              "from": start_date}
    failures = 0
    xml_data = []
    while True:
        # Send the request.
        r = requests.post(url, data=params)
        code = r.status_code

        # Asked to retry
        if code == 503:
            to = int(r.headers["retry-after"])
            logging.info("Got 503. Retrying after {0:d} seconds.".format(to))

            time.sleep(to)
            failures += 1
            if failures >= max_tries:
                logging.warn("Failed too many times...")
                break

        elif code == 200:
            failures = 0

            # Write the response to a file.
            content = r.text
            xml_data.append(content)

            # Look for a resumption token.
            token = resume_re.search(content)
            if token is None:
                break
            token = token.groups()[0]

            # If there isn't one, we're all done.
            if token == "":
                logging.info("All done.")
                break

            logging.info("Resumption token: {0}.".format(token))

            # If there is a resumption token, rebuild the request.
            params = {"verb": "ListRecords", "resumptionToken": token}

            # Pause so as not to get banned.
            to = 20
            logging.info("Sleeping for {0:d} seconds so as not to get banned."
                         .format(to))
            time.sleep(to)

        else:
            # Wha happen'?
            r.raise_for_status()

    return xml_data


def parse(xml_data):
    tree = ET.fromstring(xml_data)
    count = 0
    for i, r in enumerate(tree.findall(record_tag)):
        arxiv_id = r.find(format_tag("id")).text
        if Abstract.query.filter_by(arxiv_id=arxiv_id).first() is not None:
            continue
        title = r.find(format_tag("title")).text
        abstract = r.find(format_tag("abstract")).text
        date = r.find(format_tag("created")).text
        license = (r.find(format_tag("license")) or NullElement).text
        authors = [((el.find(format_tag("forenames")) or NullElement).text,
                    (el.find(format_tag("keyname")) or NullElement).text)
                   for el in r.findall(format_tag("author"))]
        categories = r.find(format_tag("categories")).text

        a = Abstract(arxiv_id, title, abstract, date, license, authors,
                     categories)
        db.session.add(a)
        count += 1
    db.session.commit()
    logging.info("{0} new abstracts".format(count))
