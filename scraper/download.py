#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility to download the metadata for every paper on the arXiv.

"""

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["download"]

import os
import re
import time
import requests

resume_re = re.compile(r".*<resumptionToken.*?>(.*?)</resumptionToken>.*")
url = "http://export.arxiv.org/oai2"


def download(basepath, max_tries=10, start_date=None):
    params = {"verb": "ListRecords", "metadataPrefix": "arXivRaw"}
    if start_date is not None:
        params["from"] = start_date

    failures = 0
    count = 0
    while True:
        # Send the request.
        r = requests.post(url, data=params)
        code = r.status_code

        # Asked to retry
        if code == 503:
            to = int(r.headers["retry-after"])
            print("Got 503. Retrying after {0:d} seconds.".format(to))

            time.sleep(to)
            failures += 1
            if failures >= max_tries:
                print("Failed too many times...")
                break

        elif code == 200:
            failures = 0

            # Write the response to a file.
            content = r.text
            count += 1
            fn = os.path.join(basepath, "raw-{0:08d}.xml".format(count))
            print("Writing to: {0}".format(fn))
            with open(fn, "w") as f:
                f.write(content)

            # Look for a resumption token.
            token = resume_re.search(content)
            if token is None:
                break
            token = token.groups()[0]

            # If there isn't one, we're all done.
            if token == "":
                print("All done.")
                break

            print("Resumption token: {0}.".format(token))

            # If there is a resumption token, rebuild the request.
            params = {"verb": "ListRecords", "resumptionToken": token}

            # Pause so as not to get banned.
            to = 20
            print("Sleeping for {0:d} seconds so as not to get banned."
                  .format(to))
            time.sleep(to)

        else:
            # Wha happen'?
            r.raise_for_status()


if __name__ == "__main__":
    import sys
    bp = sys.argv[1]
    try:
        os.makedirs(bp)
    except os.error:
        pass
    download(bp)
