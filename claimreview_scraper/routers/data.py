import os
import json
import glob
import requests
from pathlib import Path
import shutil
import datetime
from typing import Dict, Optional
from fastapi import APIRouter
from starlette.responses import FileResponse
from pydantic import BaseModel

from ..processing import utils, extract_claim_reviews, extract_tweet_reviews, database_builder
from .. import scrapers
from ..publishing import github

router = APIRouter()

MISINFO_BACKEND = os.environ.get('MISINFO_BACKEND', None)
print('MISINFO_BACKEND', MISINFO_BACKEND)
base_path = os.getcwd()
folder = 'data'
index_path = f'{folder}/index.json'
latest_data_path = f'{folder}/latest'


class StatsBody(BaseModel):
    date: str
    scrapers_stats: Dict[str, int]
    claim_reviews: Dict[str, int]
    tweet_reviews: Dict[str, int]
    files: Dict[str, str]

@router.get('/')
def list_data(since: Optional[str] = None, until: Optional[str] = None):
    if os.path.isfile(index_path):
        items = utils.read_json(index_path)
    else:
        items = {}
    # TODO filtering since and until
    if since:
        items = {k:v for k,v in items.items() if k >= since}
    if until:
        items = {k:v for k,v in items.items() if k <= until}
    return items

# @router.get('/latest')
# def get_latest_data():
#     pass

@router.get('/{date}')
def get_data(date: str = 'latest', file: Optional[str] = None):
    # if date == 'latest':
    # convert latest ?
    data_entries = list_data()
    if date not in data_entries:
        # TODO manage errors
        return "nothing for that date"
    data = data_entries[date]
    if not file:
        return data
    if file not in data:
        # TODO manage errors
        return "no such file, remove this parameter to see the available files"
    # extension = 'zip' if file == 'zip' else 'json'
    # file_name = file if file != 'zip' else date
    file_name = data[file]
    file_path = f'{folder}/{date}/{file_name}'
    print(file_path)
    if not os.path.isfile(file_path):
        # TODO manage errors
        return "file not found on disk"
    file_response = FileResponse(file_path, filename=file_name)
    return file_response

@router.post('/download')
def download_data(stats: StatsBody):
    # download asset
    date = stats.date
    asset_name =f'{date}.zip'
    asset_path = f'{folder}/{asset_name}'
    bytes_assets = github.get_release_asset_from_tag(date, asset_name)
    with open(asset_path, 'wb') as f:
        f.write(bytes_assets)
    shutil.unpack_archive(asset_path, folder)

    # update index
    index = list_data()
    stats = stats.dict()
    index[date] = stats
    index['latest'] = stats
    utils.write_json_with_path(index, Path(folder), 'index.json')

    # load into DB
    # get_data(date, 'claimreviews')
    with open(stats['files']['claim_reviews_raw']) as f:
        claimreviews_raw = json.load(f)
    database_builder.add_claimreviews_raw(claimreviews_raw)


@router.post('/update')
def update_data():
    # already checked up that this is ROLE==full
    # if main.ROLE == 'light':
    #     raise ValueError('light instance cannot update')
    result_stats = {}
    today = datetime.datetime.today().strftime('%Y_%m_%d')  # TODO yyyy_mm_dd
    print('today', today)
    zip_path = f'{folder}/{today}.zip'
    today_path = f'{folder}/{today}'

    # run scrapers
    stats_scrapers = scrapers.scrape_daily()
    result_stats['scrapers_stats'] = stats_scrapers
    # extract
    # TODO keep stats
    cr_stats = extract_claim_reviews.extract_ifcn_claimreviews()
    tw_stats = extract_tweet_reviews.extract() # TODO this is the slowest, keep the tweets cached in twitter_connector
    result_stats['claim_reviews'] = cr_stats
    result_stats['tweet_reviews'] = tw_stats

    # copy latest to today folder
    if os.path.isdir(today_path):
        shutil.rmtree(today_path)
    shutil.copytree(latest_data_path,today_path)

    # zip everything
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    make_archive(today_path, f'{today_path}.zip')


    files = glob.glob(f'{today_path}/**')
    files = {f.split('/')[-1].replace('.json', ''): f for f in files}
    files['zip'] = zip_path

    result_stats['files'] = files

    # save index
    index = list_data()
    index[today] = result_stats
    index['latest'] = result_stats
    utils.write_json_with_path(index, Path(folder), 'index.json')

    try:
        github.create_release(date=today)
        result_stats['date'] = today
        notify_light_instance(result_stats)
    except Exception as e:
        print(e)

    return result_stats

def notify_light_instance(stats):
    """send a POST request to misinfome data update"""
    requests.post(f'{MISINFO_BACKEND}/misinfo/api/data/update', json=stats)


def make_archive(source, destination):
    # http://www.seanbehan.com/how-to-use-python-shutil-make_archive-to-zip-up-a-directory-recursively-including-the-root-folder/
    base = os.path.basename(destination)
    name = base.split('.')[0]
    format = base.split('.')[1]
    archive_from = os.path.dirname(source)
    archive_to = os.path.basename(source.strip(os.sep))
    print(source, destination, archive_from, archive_to)
    shutil.make_archive(name, format, archive_from, archive_to)
    shutil.move('%s.%s'%(name,format), destination)