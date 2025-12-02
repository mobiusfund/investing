info = '''
simst - Sim Strat, version 1.3.4
Copyright © 2025 Mobius Fund
Author: Jake Fan, jake@mobius.fund
License: The MIT License

Usage:  simst strategies_csv [option...]
        simst -h

Options:
        -f initial_fund
        -e end_date
        -c clip_outliers
        -w window_size
        -h
-f, --fund      initial fund, overrides the fund column in the csv file
-e, --end       end date that differs from yesterday
-c, --clip      clip daily profit outliers, default 2 days
-w, --win       score rolling window size, default 30 days
-h, --help      print this message and exit

Examples:
        simst ../strat/simst.csv
        simst /tmp/test.csv -f 5000 -e 2025-06-30 -c 0 -w 365

Environment variables:
        # no db fetching
        SIMST_NO_FETCH
        # replace const.py
        SIMST_PNL_DIR
        SIMST_VALI_TAKE
        SIMST_CLIP_OUTLIERS
        SIMST_CLIP_DEFAULT
        SIMST_RISK_INIT_DTAO
        SIMST_RISK_INIT_STK
        SIMST_WIN_SIZE_DTAO
        SIMST_WIN_SIZE_STK

Notes: The strategies csv file has 6 effective columns: uid, date, block,
init, fund, strat. Other columns are allowed but ignored. A strategy is
uniquely identified by the 'uid' column. The 'init' and 'fund' columns are
only effective once and ignored by subsequent rebalancing.

Block-level precision may be simulated using Pandas 'interpolate()', if a
given block is not found in available market data. By default, simst comes
with an auto updated market database with hourly precision for dtao, and
30-minute precision for stocks.

This tool is a part of Bittensor subnet 88 - Investing, the world's first
Decentralized AUM. Please visit:

https://github.com/mobiusfund/investing
'''

import os, sys, time
import json, requests
import numpy as np
import pandas as pd
import sqlalchemy as sql
from .const import *

kk = ['uid', 'hotkey']
kb = [*kk, 'block']
kn = [*kk, 'netuid']
cd = os.path.dirname(os.path.realpath(__file__))
an = 2

class SimSt():
    def __init__(self, st=pd.DataFrame()):
        self.st = st.copy()
        self.db = self.fetchdb()
        self.rv = self.db[0][:0]
        self.fi = self.initfund()
        self.sh = pd.DataFrame(columns=[*kk, 'date', 'netuid', 'block', 'price'])
        self.ba = pd.DataFrame(columns=[*kk, 'date', 'netuid', 'block_close', 'alpha_close', 'swap_close'])
        self.hl = pd.read_csv(f'{cd}/db/ochl.col')
        self.pl = pd.read_csv(f'{cd}/db/pnl.col')
        self.sc = pd.read_csv(f'{cd}/db/score.col')

def ddclean(dd):
    if not len(dd): return dd
    dd = dd.drop_duplicates(['block', 'ochl'], keep='last')
    dd.iloc[:,1:5] = dd.iloc[:,1:5].astype(int)
    dd = dd.sort_values('block').reset_index(drop=True)
    dd.iloc[:,5:-1] = dd.iloc[:,5:-1].astype(float).interpolate().bfill().ffill()
    dd = dd.drop(dd[dd['ochl'] == 'o'].index[1:])
    dd = dd.drop(dd[dd['ochl'] == 'high'].sort_values('price').index[:-1])
    dd = dd.drop(dd[dd['ochl'] == 'low'].sort_values('price').index[1:])
    dd = dd.drop(dd[dd['ochl'] == 'c'].index[:-1])
    dd['ochl'] = dd['ochl'].str.replace('hour', 'time')
    return dd

def ddclean1(dd, b):
    if not len(dd): return dd
    dd = dd.drop_duplicates(['block', 'ochl'], keep='last')
    netuid = dd['netuid'].iat[0]
    day = dd[dd['ochl'] == 'day']
    dd = pd.concat([dd[dd['ochl'] != 'day'], b[~b['block'].isin(dd['block'])]])
    dd = dd.sort_values('block').reset_index(drop=True)
    dd.loc[dd['netuid'] != netuid, dd.columns[3:-1]] = float('nan')
    dd.loc[[0, len(dd)-1], 'price'] = day[['open', 'close']].iloc[-1].values
    dd.iloc[:,3:-1] = dd.iloc[:,3:-1].astype(float).interpolate().bfill().ffill()
    dd['netuid'] = netuid
    return dd

def fetchda(self, a):
    if a not in asst(self.st): return pd.DataFrame()
    st = self.st
    date = st['date'].min()
    db = f'{cd}/db/daily{a or ""}.db'
    conn = sql.create_engine(f'sqlite:///{db}').connect()
    if not os.path.getsize(db):
        pd.read_csv(f'{db[:-3]}.00').to_sql('bndaily', conn, index=False)
    bn = pd.read_sql('SELECT * FROM bndaily', conn)
    last = bn['date'].iat[-1] if len(bn) > 1 else FIRST_DATE
    if last >= time.strftime('%F', time.gmtime(time.time() - 86400 - 18000)) or self.no_fetch:
        return bn[bn['date'] >= date]

    print(f'Fetching {db.split("/")[-1]}, begin {last}...', end='', flush=True)
    try: r, e = json.loads(requests.get(f'{API_ROOT}/daily{a or ""}/{last}').json()), 'done'
    except: r, e = [], 'error'
    df = pd.DataFrame(r, None, bn.columns).astype(bn.dtypes)
    if len(bn) > 1: df = df[df['date'] > last]
    bn = pd.concat([bn, df])
    print(f" {e}, end {bn['date'].iat[-1] if len(bn) > 1 else last}.")
    df.to_sql('bndaily', conn, if_exists='append', index=False)
    conn.commit()
    return bn[bn['date'] >= date]

def fetchdb(self):
    if not len(self.st): return [pd.DataFrame()] * an
    st = self.st
    fd = [self.fetchda(a) for a in range(an)]
    if len(fd[1]): fd[1].insert(3, 'price', fd[1]['open'])
    for da in ['split', 'dividend'] if len(fd[1]) else []:
        db = f'{cd}/db/{da}.db'
        conn = sql.create_engine(f'sqlite:///{db}').connect()
        try: r = json.loads(requests.get(f'{API_ROOT}/{da}').json())
        except: r = []
        df = pd.DataFrame(r, None, pd.read_csv(f'{db[:-3]}.col').columns)
        if len(df): df.to_sql(da, conn, if_exists='replace', index=False)
        conn.commit()
        try: df = pd.read_sql(f'SELECT * FROM {da}', conn)
        except: pass
        fd.append(df)
    return fd

def initfund(self):
    st = self.st
    notin = 'init' not in st
    anum0 = {}
    fi = pd.DataFrame(columns=[*kk, 'date', 'block', 'init', 'fund', 'strat', 'a'])
    if not len(st): return fi
    st['strat'] = st['strat'].str.replace(r'''[^{'\w":.,}\[\]\*=+-]''', '', regex=True)
    for _, di in st.sort_values(['date', 'block']).iterrows():
        uid = di['uid']
        try: strat = eval(di['strat'])
        except: continue
        if type(strat) is not dict: continue
        anum = asset(strat)
        if anum not in range(an): continue
        if uid not in anum0: anum0[uid] = anum
        if anum != anum0[uid]: continue
        try: asum = sum([abs(strat[k]) for k in strat if k not in ['_', '*', '=', '-+']])
        except: continue
        if asum > 1: continue
        bn = self.db[anum]
        if not len(bn): continue
        date = max(bn['date'].iat[0], di['date'])
        block = bn[bn['date'] >= date]['block'].iat[0] if notin else di['block']
        init = int(uid not in fi['uid'].values) if notin else di['init']
        hk = '' if 'hotkey' not in st else di['hotkey']
        fi.loc[len(fi)] = uid, hk, date, block, init, *di[['fund', 'strat']], anum
    fi = fi.drop_duplicates(kb)
    if not len(self.db[0]): return fi

    bn, fn = self.db[0], fi[fi['a'] == 0]
    self.rv = bn[bn['block'].isin(fn['block'])].copy()
    tempo = bn[['netuid', 'tempo']].drop_duplicates().set_index('netuid').to_dict()['tempo']
    rv = self.rv[:0].copy()
    for date, block in fn[['date', 'block']].values:
        for n in [n for n in bn['netuid'].unique() if n not in bn[bn['block'] == block]['netuid'].values]:
            rv.loc[len(rv)] = date, block, n, tempo[n], -1, *[float('nan')] * len(rv.columns[5:])
    self.rv = pd.concat([self.rv, rv])
    self.rv['ochl'] = 'rv'
    return fi

def fadaily(self, date, a):
    bn, fi = self.db[a], self.fi
    fa = pd.DataFrame(columns=[*kk, 'block', 'netuid', 'init', 'fund', 'alloc'])
    for _, di in fi[(fi['date'] == date) & (fi['a'] == a)].iterrows():
        strat = eval(di['strat'])
        strat = {k:strat[k] for k in strat if k and k in bn[bn['date'] == date]['netuid'].values}
        if not a: strat = {k:v for k,v in strat.items() if v > 0}
        strat[a and ''] = 1 - sum([abs(v) for v in strat.values()])
        for n in strat: fa.loc[len(fa)] = *di[kb], n, *di[['init', 'fund']], strat[n]
    return fa

def pldaily(self, date, a=0):
    if not len(self.db[a]): return
    bn, rv, ba = self.db[a], self.rv, self.ba
    fa = self.fadaily(date, a)
    bb = fa[kb].drop_duplicates().sort_values(kb)
    nn = pd.concat([ba[kn], fa[kn]]).drop_duplicates().sort_values(kn).reset_index()
    dn = pd.concat([bn[bn['date'] == date], rv[rv['date'] == date]])
    ba, fa = ba.set_index(kn).sort_index(), fa.set_index(kb).sort_index()

    alpha0k = {}
    dg = pd.DataFrame()
    for i in nn.index:
        uid, hk, netuid = key = tuple(nn.loc[i,kn])
        blk = bb[(bb['uid'] == uid) & (bb['hotkey'] == hk)]['block']
        dd = ddclean(dn[dn['netuid'] == netuid])
        dd = dd[(dd['ochl'] != 'rv') | dd['block'].isin(blk)]
        if not len(dd): continue
        try: block0, alpha0 = ba.loc[key].iloc[-3:-1]
        except: block0, alpha0 = dd['block'].iat[0], 0.0
        blocks = dd['block'].diff()
        blocks.iat[0] = dd['block'].iat[0] - block0
        dd.loc[dd['emission'].isna(), 'emission'] = 0
        dd.loc[dd['weight'].isna() | (dd['weight'] == 0), 'weight'] = 1e18
        bbdiv = list(dd['emission'] * (1 - self.vali_take) * blocks / (dd['tempo'] + 1) / dd['weight'])
        alpha = [alpha0 * (1 + bbdiv[0])]
        for i in range(1, len(dd)): alpha.append(alpha[i-1] * (1 + bbdiv[i]))
        alpha0k[key] = alpha0
        dd['bbdiv'] = bbdiv
        dd['alpha'] = alpha
        dd['value'] = dd['alpha'] * dd['price']
        dd['swap'] = [float('nan')] * len(dd)
        dd['init'] = 0.0
        dd.insert(0, 'hotkey', hk)
        dd.insert(0, 'uid', uid)
        dg = pd.concat([dg, dd])

    ndl, self._dl = ba.index.droplevel, []
    for key in ba[ndl([1,2]).isin(dg['uid']) & ~ndl([0,1]).isin(dg['netuid'])].index if len(dg) else []:
        alpha0k[(*key[:2], 0)] = alpha0k.get((*key[:2], 0), 0) + ba.loc[key].iat[-1]
        self._dl += [key]

    dh = pd.DataFrame()
    for gg, dd in dg.groupby(kb) if len(dg) else []:
        uid, hk, block = gg
        dd = dd.reset_index(drop=True)
        rev = 'rv' in dd['ochl'].values
        dd['alpha'] = dd['netuid'].map(lambda n: alpha0k[(uid, hk, n)]) * (1 + dd['bbdiv'])
        dd['value'] = dd['alpha'] * dd['price']
        dd['swap'] = dd['tao_in'] - dd['tao_in'] * dd['alpha_in'] / (dd['alpha_in'] + dd['alpha'])
        dd.loc[dd['netuid'] == 0, 'swap'] = dd['alpha']

        swap = dd.drop_duplicates(kn)['swap'].sum()
        for i in dd.index:
            di = dict(dd.loc[i])
            netuid = di['netuid']
            key = uid, hk, netuid
            if rev:
                try: init, fund, alloc = fa.loc[[gg]].set_index('netuid').loc[netuid]
                except: init, fund, alloc = 0, 0, 0
                if not init and fund and alloc: self.stupdate(gg, swap)
                diffs = (init * fund or swap) * alloc - di['swap']
                if di['tao_in'] + diffs <= 0 and netuid: diffa = -di['alpha']
                else: diffa = di['alpha_in'] - di['tao_in'] * di['alpha_in'] / (di['tao_in'] + diffs) if netuid else diffs
                di['alpha'] += diffa - abs(diffa) * di['emission'] / di['weight']
                if di['alpha'] < 0: di['alpha'] = 0
                dd.loc[i,'alpha'] = di['alpha']
                dd.loc[i,'value'] = di['alpha'] * di['price']
                dd.loc[i,'swap'] = di['tao_in'] - di['tao_in'] * di['alpha_in'] / (di['alpha_in'] + di['alpha']) if netuid else di['alpha']
                dd.loc[i,'init'] = init * fund * alloc
            alpha0k[key] = di['alpha']
        dh = pd.concat([dh, dd])
    self.pltotal(dh, date, a)

def pldaily1(self, date, a=1):
    if not len(self.db[a]): return
    bn, sh, ba = self.db[a], self.sh, self.ba
    fa = self.fadaily(date, a)
    nn = pd.concat([ba[kn], fa[kn]]).drop_duplicates().sort_values(kn).reset_index()
    dn = bn[bn['date'] == date]
    sh = sh.drop_duplicates(kn, keep='last').set_index(kn)
    ba, fa = ba.set_index(kn).sort_index(), fa.set_index(kk).sort_index()

    day = dn[dn['ochl'] == 'day']
    ben = dn[(dn['ochl'] != 'day') & (dn['netuid'] == STK_BENCH)]
    one = ben.copy()
    one['netuid'], one.iloc[:,3:-1] = '', 1
    spl, div = self.db[-2:]
    spl, div = spl[spl['date'] == date], div[div['ex_date'] == date]
    bk0, bk1 = ben['block'].iloc[[0, -1]] if len(ben) else [0, 0]

    alpha0k = {}
    dg = pd.DataFrame()
    for i in nn.index:
        uid, hk, netuid = key = tuple(nn.loc[i,kn])
        dd = ddclean1(dn[dn['netuid'] == netuid], ben)
        if netuid == '': dd = one.copy()
        if not len(dd): continue
        try: alpha0 = ba.loc[key].iat[-2]
        except: alpha0 = 0.0
        try: spli, spl2 = spl[spl['netuid'] == netuid][['from', 'to']].iloc[-1]
        except: spli, spl2 = 0, 0
        try: divd, curr = div[div['netuid'] == netuid][['amount', 'currency']].iloc[-1]
        except: divd, curr = 0, ''
        if spli and spl2: alpha0 *= spl2 / spli
        if curr and curr != 'USD': pass
        if divd and curr:
            price = sh.loc[key]['price'] if alpha0 < 0 else dd['price'].iat[0]
            if alpha0 < 0: sh.loc[key] = date, bk0, price - divd
            if alpha0 > 0: alpha0 *= 1 + divd / price
        alpha0k[key] = alpha0
        dd['alpha'] = alpha0
        dd['value'] = alpha0 * dd['price']
        dd['swap'] = dd['value']
        dd['init'] = 0.0
        dd.insert(0, 'hotkey', hk)
        dd.insert(0, 'uid', uid)
        dg = pd.concat([dg, dd])

    ndl, self._dl = ba.index.droplevel, []
    for key in ba[ndl([1,2]).isin(dg['uid']) & ~ndl([0,1]).isin(dg['netuid'])].index if len(dg) else []:
        alpha0k[(*key[:2], '')] = alpha0k.get((*key[:2], ''), 0) + ba.loc[key].iat[-1]
        self._dl += [key]

    dh = pd.DataFrame()
    for gg, dd in dg.groupby(kb) if len(dg) else []:
        uid, hk, block = gg
        dd = dd.reset_index(drop=True)
        dd['alpha'] = dd['netuid'].map(lambda n: alpha0k[(uid, hk, n)])
        dd['value'] = dd['alpha'] * dd['price']
        short = dd[dd['alpha'] < 0]['netuid'].map(lambda n: sh.loc[(uid, hk, n)]['price'])
        if len(short): dd.loc[dd['alpha'] < 0, 'value'] -= dd['alpha'] * short * 2
        dd.loc[(dd['alpha'] < 0) & (dd['value'] < 0), ['alpha', 'value']] = 0
        dd['swap'] = dd['value']
        fb = []
        if block == bk0 and gg[:2] in fa.index:
            fb = fa.loc[[gg[:2]]]
            fb = fb[fb['block'] < bk0 - -STK_MOO]
            fb['init'] = int(1 in fb['init'].values)
            if len(fb): fb = fb[fb['block'] == fb['block'].iat[-1]]
        if block == bk1 and gg[:2] in fa.index:
            fb = fa.loc[[gg[:2]]]
            fb = fb[(bk0 - -STK_MOO <= fb['block']) & (fb['block'] < bk1 - -STK_MOC)]
            fb['init'] = int(1 in fb['init'].values)
            if len(fb): fb = fb[fb['block'] == fb['block'].iat[-1]]
        if block == bk1 and gg[:2] in fa.index and not len(fb):
            fb = fa.loc[[gg[:2]]]
            fb = fb[fb['block'] >= bk1 - -STK_MOC]
            fb['init'] = int(1 in fb['init'].values)
            if len(fb): fb = fb[fb['block'] == fb['block'].iat[-1]][-1:]
            if 1 in fb['init'].values: fb['netuid'], fb['alloc'] = '', 1
            else: fb = []

        swap = dd.drop_duplicates(kn)['swap'].sum()
        for i in dd.index:
            di = dict(dd.loc[i])
            netuid = di['netuid']
            key = uid, hk, netuid
            if len(fb):
                try: blk, init, fund, alloc = fb.set_index('netuid').loc[netuid]
                except: blk, init, fund, alloc = 0, 0, 0, 0
                if not init and fund and alloc: self.stupdate((*gg[:2], blk), swap)
                alpha = (init * fund or swap) * alloc / di['price']
                diffa = alpha - di['alpha']
                di['alpha'] = alpha - abs(diffa) * STK_FEE / di['price'] * (alloc >= 0) * bool(netuid)
                short = di['price'] + abs(diffa) * STK_FEE / di['alpha'] if alloc <  0 else 0
                if di['alpha'] < 0 and alloc >= 0: di['alpha'] = 0
                if di['alpha'] > 0 and alloc <  0: di['alpha'] = 0
                if di['alpha'] < 0: sh.loc[key] = date, block, short
                dd.loc[i,'alpha'] = di['alpha']
                dd.loc[i,'value'] = di['alpha'] * (di['price'] - short * 2)
                dd.loc[i,'swap'] = di['alpha'] * (di['price'] - short * 2)
                dd.loc[i,'init'] = abs(init * fund * alloc)
            alpha0k[key] = di['alpha']
        dh = pd.concat([dh, dd])
    self.sh = sh.reset_index()[self.sh.columns]
    self.pltotal(dh, date, a, ben)

def pltotal(self, dh, date, a, b=[]):
    if not hasattr(self, '_hl'):
        self._hl = self.hl[:0].copy()
    bn, df, hl, pl = self.db[a], self._hl, self.hl, self.pl
    nn = [*bn['netuid'].unique(), *([''] if a else [])]
    col = ['block', 'price', 'alpha', 'value', 'swap']

    for _, di in hl[hl['netuid'].isin(nn)].iterrows() if not len(dh) else []:
        df.loc[len(df)] = di

    for gg, dd in dh.groupby(kn) if len(dh) else []:
        dd = dd.reset_index(drop=True)
        if dd['init'].any():
            dd.loc[dd['init'] > 0, ['value', 'swap']] = dd['init']
            dd = dd[dd['block'] >= dd[dd['init'] > 0]['block'].iat[0]]
        loc  = [dd.iloc[0][col]]
        loc += [dd[dd['swap'] == dd['swap'].max()].iloc[-1][col]]
        loc += [dd[dd['swap'] == dd['swap'].min()].iloc[-1][col]]
        loc += [dd.iloc[-1][col]]
        df.loc[len(df)] = *gg[:2], date, gg[2], *[a for z in zip(*loc) for a in z]

    for gg in self._dl:
        df.loc[len(df)] = *gg[:2], date, gg[2], *[0] * 20

    for gg, dd in dh.groupby(kk) if len(dh) else []:
        dd = dd.reset_index(drop=True)
        if dd['init'].any():
            dd.loc[dd['init'] > 0, ['value', 'swap']] = dd['init']
            dd = dd[dd['block'] >= dd[dd['init'] > 0]['block'].iat[0]]
        if not a: dd = dd[dd['ochl'].isin(['o', 'c', 'time', 'rv'])]
        if len(b): dd = dd[dd['block'].isin(b['block'])]
        dd = dd.drop_duplicates(['block', 'netuid'])
        dd = dd[kb + col[-2:]].groupby(kb).sum().reset_index()
        loc  = [dd.iloc[0,-3:]]
        loc += [dd[dd['swap'] == dd['swap'].max()].iloc[-1,-3:]]
        loc += [dd[dd['swap'] == dd['swap'].min()].iloc[-1,-3:]]
        loc += [dd.iloc[-1,-3:]]
        pl.loc[len(pl)] = *gg, date, a, *[a for z in zip(*loc) for a in z]

def plfinal(self):
    if not hasattr(self, '_hl'): return
    self.hl = hl = self._hl
    self.ba = hl[(hl['alpha_close'].abs() > 1e-6) | (hl.loc[:,'block_open':].abs().sum(1) == 0)][self.ba.columns]
    self.shappend(self.sh)
    self.hlappend(self.hl)
    self.plappend(self.pl)
    delattr(self, '_hl')

def pl2sc(self):
    pl, sc = self.pl, self.sc
    pl = pl.sort_values([*pl.columns[:3]])
    for gg, dd in pl.groupby([*pl.columns[:2]]) if len(pl) else []:
        date, a, days = dd['date'].iat[-1], dd['asset'].iat[0], len(dd)
        dd = dd[-self.win_size[a]:].reset_index(drop=True)
        init = dd['swap_open'].iat[0]
        dd['pnl'] = dd['swap_close'].diff()
        dd['pnl%'] = dd['pnl'] / dd['swap_close'].shift() * 100
        dd['pnl'].iat[0] = dd['swap_close'].iat[0] - init
        dd['pnl%'].iat[0] = dd['pnl'].iat[0] / init * 100

        ii = dd[dd['pnl%'] > 0].sort_values('pnl%')[::-1][:self.clip_outliers + 1].index
        if len(ii) == 0: clip = 0
        elif len(ii) == self.clip_outliers + 1: clip = dd['pnl%'][ii[-1]]
        else: clip = min(self.clip_default, dd['pnl%'][ii[-1]])
        dd.loc[ii, 'pnl%'] = clip
        for i in ii:
            open = dd['swap_close'][i-1] if i else init
            dd.loc[i:, 'swap_close'] -= dd['swap_close'][i] - open * (1 + clip / 100)
            dd.loc[i, 'pnl'] = open * clip / 100
        sc.loc[len(sc)] = *gg, date, a, days, *score(dd, self.risk_init[a])[1:]
    #sc.loc[sc['days'] < DAYS_FINAL, 'score'] *= sc['days'] / (sc['days'] + DAYS_INIT)
    sc.loc[sc['days'] < DAYS_FINAL, 'score'] *= (sc['days'] / DAYS_FINAL) ** DAYS_DELAY
    self.sc = sc.sort_values(['score', 'return%'], ascending=False)
    self.scappend(sc)

def sc2pct(self):
    sc = self.sc.copy()
    j3 = ['value', 'swap']
    j2 = ['score', 'mar']
    jp = [j for j in sc.columns if j[-1:] == '%' and j != 'daily%']
    sc[j3] = sc[j3].map('{:.3e}'.format)
    sc[j2] = sc[j2].map('{:.2f}'.format)
    sc[jp] = sc[jp].map('{:.2f}%'.format)
    sc['lsr'] = sc['lsr'].map('{:.4f}'.format)
    sc['daily%'] = sc['daily%'].map('{:.4f}%'.format)
    if not sc['hotkey'].sum(): sc = sc.drop('hotkey', axis=1)
    return sc

def asst(st):
    aa = []
    for strat in st['strat'] if 'strat' in st else []:
        try: a = asset(eval(strat))
        except: continue
        if a not in aa: aa.append(a)
    return aa

def asset(x): return x.get('_', 0)

def kelly(p, b): return (p * (b + 1) - 1) / b

def drawdown(pnl):
    peak, down = 0, 0
    gain = list(pnl.cumsum())
    for i in range(len(gain)):
        peak = max(peak, gain[i])
        down = max(down, peak - gain[i])
    return down

def score(dd, risk_init=1):
    days = len(dd)
    prob = len(dd[dd['pnl%'] > 0]) / days
    pavg = dd['pnl%'][dd['pnl%'] > 0].mean()
    lavg = dd['pnl%'][dd['pnl%'] < 0].mean() * -1
    value = dd['value_close'].iat[-1]
    swap = dd['swap_close'].iat[-1]
    init = dd['swap_open'].iat[0]
    gain = max(swap - init, -init) / init * 100
    risk = drawdown(dd['pnl%'])
    daily = ((1 + gain / 100) ** (1 / days) - 1) * 100
    apr = ((1 + daily / 100) ** 365 - 1) * 100
    mar = gain / max(risk, risk_init / days ** 0.5)
    lsr = dd['pnl'].sum() / (dd['pnl'].abs().sum() or 1e18)
    odds = 50 + kelly(prob, pavg / lavg) / 2 * 100
    if odds <= 0: odds = 0
    if np.isnan(odds): odds = prob * 100
    score = mar * lsr * odds * daily
    if score <= 0: score = 0
    return days, value, swap, score, apr, lsr, mar, risk, odds, daily, gain

def args():
    cwd = ''
    if (sys.argv[-1][:2] + sys.argv[-1][-1:]) == '///': cwd = sys.argv.pop()[1:]
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']: print(info), exit()
    if len(sys.argv) == 1: print('simst - Sim Strat\n')

    import argparse
    parser = argparse.ArgumentParser(
        prog = 'simst',
        usage = 'simst strategies_csv [option...]',
        add_help = False,
    )
    parser.add_argument('csv', metavar='strategies_csv')
    parser.add_argument('-f', '--fund', default=0, type=float)
    parser.add_argument('-e', '--end', default='')
    parser.add_argument('-c', '--clip', default=-1, type=int)
    parser.add_argument('-w', '--win', default=0, type=int)
    parser.add_argument('-h', '--help', action='store_true')

    try: a = parser.parse_args()
    except: print("Try 'simst -h' for more info", file=sys.stderr), exit(1)
    csv = (cwd if a.csv[:1] != '/' else '') + a.csv
    if not os.path.isfile(csv) or not os.access(csv, os.R_OK):
        print(f"simst: error: unable to read file '{a.csv}'", file=sys.stderr)
        exit(1)
    return csv, a.fund, a.end, a.clip, a.win

def main():
    csv, fund, end, clip, win = args()
    sim = SimSt(pd.read_csv(csv))
    if fund: sim.fi['fund'] = fund
    if clip >= 0: sim.clip_outliers = clip
    if win: sim.win_size = [win] * an
    if end:
        sim.db[:an] = [bn[bn['date'] <= end] if len(bn) else bn for bn in sim.db[:an]]
    dates = sorted(set([d for bn in sim.db[:an] if len(bn) for d in bn['date'].values]))
    for date in dates:
        print(date, end='', flush=True)
        sim.pldaily(date)
        sim.pldaily1(date)
        sim.plfinal()
        print(', ' if date < dates[-1] else '.\n', end='', flush=True)
    sim.pl2sc()
    if sim.pnl_dir: sim.pl.to_csv(f'{sim.pnl_dir}/PnL_{os.path.basename(csv)}')
    if not len(sim.sc): return
    print(f'clip outlier days: {sim.clip_outliers}, rolling window days: {sim.win_size}')
    print(sim.sc2pct().to_string(index=False))

def concat(ls):
    ds = [df for df in ls if len(df)]
    return _concat(ds) if len(ds) else ls[0].copy()
pd.concat, _concat = concat, pd.concat

# reserved for live api server
def stupdate(self, g, v): pass
def shappend(self, sh): pass
def hlappend(self, hl): pass
def plappend(self, pl): pass
def scappend(self, sc): pass

SimSt.fetchda = fetchda
SimSt.fetchdb = fetchdb
SimSt.initfund = initfund
SimSt.fadaily = fadaily
SimSt.pldaily = pldaily
SimSt.pldaily1 = pldaily1
SimSt.pltotal = pltotal
SimSt.plfinal = plfinal
SimSt.pl2sc = pl2sc
SimSt.sc2pct = sc2pct
SimSt.stupdate = stupdate
SimSt.shappend = shappend
SimSt.hlappend = hlappend
SimSt.plappend = plappend
SimSt.scappend = scappend

SimSt.no_fetch = bool(os.getenv('SIMST_NO_FETCH', False))
SimSt.pnl_dir = os.getenv('SIMST_PNL_DIR', PNL_DIR)
SimSt.vali_take = float(os.getenv('SIMST_VALI_TAKE', VALI_TAKE))
SimSt.clip_outliers = int(os.getenv('SIMST_CLIP_OUTLIERS', CLIP_OUTLIERS))
SimSt.clip_default = int(os.getenv('SIMST_CLIP_DEFAULT', CLIP_DEFAULT))
SimSt.risk_init = []
SimSt.risk_init += [float(os.getenv('SIMST_RISK_INIT_DTAO', RISK_INIT_DTAO))]
SimSt.risk_init += [float(os.getenv('SIMST_RISK_INIT_STK', RISK_INIT_STK))]
SimSt.win_size = []
SimSt.win_size += [int(os.getenv('SIMST_WIN_SIZE_DTAO', WIN_SIZE_DTAO))]
SimSt.win_size += [int(os.getenv('SIMST_WIN_SIZE_STK', WIN_SIZE_STK))]

if __name__ == "__main__": main()
