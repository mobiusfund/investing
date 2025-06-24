# Copyright © 2025 Mobius Fund

import os, sys
import json, requests
import traceback
import pandas as pd
import bittensor as bt
from .const import API_ROOT

cd = os.path.dirname(os.path.realpath(__file__))

def rev(ss58):
    bt.logging.info(f'Submitting strategy {ss58}...')
    strat = open(f'{cd}/../strat/{ss58}').read()
    data = {'ss58': ss58, 'strat': strat}
    try: r = requests.post(f'{API_ROOT}/rev', json=data)
    except:
        traceback.print_exc(1, file=sys.stdout)
        return
    if r.status_code <= 201:
        os.utime(f'{cd}/../strat/.last-update')
    btlog(r)

def pnl():
    bt.logging.info('Fetching PnL data...')
    pl = pd.read_csv(f'{cd}/db/pnl.col')
    try: r = requests.get(f'{API_ROOT}/pnl')
    except:
        traceback.print_exc(1, file=sys.stdout)
        return pl
    if r.status_code == 200:
        pl = pd.DataFrame(json.loads(r.json()), None, pl.columns)
    btlog(r)
    return pl

def days():
    bt.logging.info('Fetching days active...')
    da = pd.read_csv(f'{cd}/db/days.col')
    try: r = requests.get(f'{API_ROOT}/days')
    except:
        traceback.print_exc(1, file=sys.stdout)
        return da
    if r.status_code == 200:
        da = pd.DataFrame(json.loads(r.json()), None, da.columns)
    btlog(r)
    return da

def dist():
    bt.logging.info('Fetching dedupe data...')
    try: r = requests.get(f'{API_ROOT}/dist')
    except:
        traceback.print_exc(1, file=sys.stdout)
        return []
    if r.status_code == 200:
        ab = json.loads(r.json())
    btlog(r)
    return ab

def btlog(r):
    if r.status_code <= 201: log = bt.logging.info
    else: log = bt.logging.error
    log(f'API: status code {r.status_code}')
    if r.status_code != 200 and r.text: log(f'API: {r.text}')
