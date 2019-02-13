#!/usr/bin/env python

import utils
import requests
import os
from bs4 import BeautifulSoup

import dateparser

LIST_URL = 'https://www.snopes.com/fact-check/page/{}/'

my_path = utils.data_location / 'snopes'

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

    for s in soup.select('main.main article.list-group-item'):
        url = s.select('a.fact_check')[0]['href']
        title = s.select('h2.card-title')[0].text.strip()
        subtitle = s.select('p.card-subtitle')
        if subtitle:
            subtitle = subtitle[0].text.strip()
        else:
            subtitle = None
        date = s.select('p.card-subtitle span.date')
        if date:
            date = date[0].text.strip()
            date = dateparser.parse(date).isoformat()
        else:
            date = None

        found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
        if found:
            print('found')
            go_on = False
            break

        all_statements.append({
            'url': url,
            'title': title,
            'subtitle': subtitle,
            'date': date,
            'source': 'snopes'
        })

    print(len(all_statements))
    page += 1


utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')