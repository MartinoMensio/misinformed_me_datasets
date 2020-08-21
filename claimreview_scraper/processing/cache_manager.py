"""
this module caches all the web GET requests using the mongo collection "cache".
"""

import requests
import os
import json
import hashlib

from pathlib import Path

from . import unshortener
from . import database_builder





def get(url, unshorten=True, force_refresh=False, verify=True, headers={}):
    if unshorten:
        url_short = url
        url = unshortener.unshorten(url_short)
    cache_hit = database_builder.cache_get(url)
    if cache_hit and not force_refresh:
        # cached
        return cache_hit['html']
    else:
        # new
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code != 200:
            print('WARN', response.status_code, 'for', url)
        html = response.text
        database_builder.cache_put(url, html)
        return html

