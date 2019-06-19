#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser

from .. import utils
from .. import claimreview

LIST_URL = 'https://www.politifact.com/truth-o-meter/statements/?page={}'
STATEMENT_SELECTOR = 'div.statement'


my_path = utils.data_location / 'politifact'

def main():
    page = 1
    if os.path.exists(my_path / 'fact_checking_urls.json'):
        all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    else:
        all_statements = []
    go_on = True
    while go_on:
        facts_url = LIST_URL.format(page)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break
        #print(response.text)
        soup = BeautifulSoup(response.text, 'lxml')
        page_number_real = soup.select('div.pagination span.step-links__current')[0].text
        if str(page) not in page_number_real:
            print(page_number_real)
            break
        statements = soup.select(STATEMENT_SELECTOR)
        #print(statements)
        for s in statements:
            url = 'https://www.politifact.com' + s.select('p.statement__text a.link')[0]['href']
            claim = s.select('p.statement__text a.link')[0].text
            author = s.select('div.statement__source a')[0].text
            label = s.select('div.meter img')[0]['alt']
            reason = s.select('div.meter p.quote')[0].text
            date = s.select('p.statement__edition span.article__meta')[0].text
            date = dateparser.parse(date).isoformat()

            found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
            if found:
                print('found')
                go_on = False
                break

            #print(link, author, rating)
            all_statements.append({
                'url': url,
                'claim': claim,
                'author': author,
                'label': claimreview.simplify_label(label),
                'original_label': label,
                'reason': reason,
                'date': date,
                'source': 'politifact'
            })

        print(len(all_statements))
        page += 1


    utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')