#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Flask
DEBUG = False
SECRET_KEY = "development key"

# Database
REDIS_PORT = 6379
REDIS_PREFIX = "arxiv"
SQLALCHEMY_DATABASE_URI = "postgresql://localhost/arxiv"

# Google OAuth stuff.
GOOGLE_OAUTH2_CLIENT_ID = None
GOOGLE_OAUTH2_CLIENT_SECRET = None
