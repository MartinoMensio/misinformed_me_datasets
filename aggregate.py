#!/usr/bin/env python

# puts together all the datasets

import os
import json
import glob
import shutil
import signal
import sys
from collections import defaultdict
from pathlib import Path

import utils
import unshortener

# decide here what to aggregate
choice = {k if 'domain_list_' not in k else 'domain_list': {
    'urls': el['contains']['url_classification'],
    'domains': el['contains']['domain_classification'],
    'rebuttals': el['contains']['rebuttal_suggestion'],
    'claimReviews': el['contains']['claimReviews']
} for k, el in utils.read_json('sources.json')['datasets'].items()}
""" {
    'datacommons_factcheck': {
        'urls': True,
        'domains': False,
        'rebuttals': True
    },
    'datacommons_feeds': {
        'urls': True,
        'domains': False,
        'rebuttals': False
    },
    'mrisdal_fakenews': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'golbeck_fakenews': {
        'urls': True,
        'domains': False,
        'rebuttals': True
    },
    'liar': {
        'urls': False,
        'domains': False,
        'rebuttals': False
    },
    'buzzface': {
        'urls': True,
        'domains': False,
        'rebuttals': False
    },
    'opensources': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'fakenewsnet': {
        'urls': True,
        'domains': False,
        'rebuttals': False
    },
    'rbutr': {
        'urls': False, # which class to assign them?
        'domains': False,
        'rebuttals': True
    },
    'hyperpartisan': {
        'urls': False, # hyperpartisan does not mean fake
        'domains': False,
        'rebuttals': False
    },
    'wikipedia': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'domain_list': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'melissa_zimdars': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'jruvika_fakenews': {
        'urls': True,
        'domains': False,
        'rebuttals': False
    },
    'factcheckni_list': {
        'urls': True,
        'domains': False,
        'rebuttals': True
    },
    'google_factcheck_explorer': {
        'urls': True,
        'domains': False,
        'rebuttals': True
    },
    'buzzfeednews': {
        'urls': False,
        'domains': True,
        'rebuttals': False
    },
    'pontes_fakenewssample': {
        'urls': True,
        'domains': False,
        'rebuttals': False
    }
}
"""
all_urls = []
all_domains = []
all_rebuttals = defaultdict(list)
all_claimreviews = []
for subfolder, config in choice.items():
    if config['urls']:
        urls = utils.read_json(utils.data_location / subfolder / 'urls.json')
        all_urls.extend(urls)
    if config['domains']:
        domains = utils.read_json(utils.data_location / subfolder / 'domains.json')
        all_domains.extend(domains)
    if config['rebuttals']:
        rebuttals = utils.read_json(utils.data_location / subfolder / 'rebuttals.json')
        for source_url, rebuttal_l in rebuttals.items():
            for rebuttal_url, source in rebuttal_l.items():
                all_rebuttals[source_url].append({
                    'url': rebuttal_url,
                    'source': source
                })
    if config['claimReviews']:
        claimReview = utils.read_json(utils.data_location / subfolder / 'claimReviews.json')
        all_claimreviews.extend(claimReview)

urls_cnt = len(all_urls)
domains_cnt = len(all_domains)
fake_urls_cnt = len([el for el in all_urls if el['label'] == 'fake'])
fake_domains_cnt = len([el for el in all_domains if el['label'] == 'fake'])
print('#urls', urls_cnt, ': fake', fake_urls_cnt, 'true', urls_cnt - fake_urls_cnt)
print('#domains', domains_cnt, ': fake', fake_domains_cnt, 'true', domains_cnt - fake_domains_cnt)

aggregated_urls = utils.aggregate(all_urls)
aggregated_domains = utils.aggregate(all_domains, 'domain')

utils.write_json_with_path(aggregated_urls, utils.data_location, 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, utils.data_location, 'aggregated_domains.json')
utils.write_json_with_path(all_rebuttals, utils.data_location, 'aggregated_rebuttals.json')
utils.write_json_with_path(all_claimreviews, utils.data_location, 'aggregated_claimReviews.json')

# copy to backend
utils.write_json_with_path(aggregated_urls, Path('../backend'), 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, Path('../backend'), 'aggregated_domains.json')
utils.write_json_with_path(all_rebuttals, Path('../backend'), 'aggregated_rebuttals.json')
utils.write_json_with_path(all_claimreviews, Path('../backend'), 'aggregated_claimReviews.json')

utils.print_stats(aggregated_urls)
utils.print_stats(aggregated_domains)

to_be_mapped = [url for url in aggregated_urls.keys()]
unshortener.unshorten_multiprocess(to_be_mapped)
