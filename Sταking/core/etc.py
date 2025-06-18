# Copyright © 2025 Mobius Fund

import os, math, requests
import pandas as pd
from .const import RAWGIT_ROOT
from .const import DD_TRIGGER, DD_POWER
from .const import DEC_UID, DEC_DECAY, DEC_CUTOFF
from .const import DAYS_FINAL
from .simst import SimSt, asset

def update():
    init = 'Sταking/__init__.py'
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    lv = open(f'{root}/{init}').read()
    rv = requests.get(f'{RAWGIT_ROOT}/refs/heads/main/{init}').text
    lv, rv = [eval(v.split('\n')[0].split('=')[1]) for v in [lv, rv]]
    ln, rn = [sum(int(n) * 100 ** i for i, n in enumerate(v.split('.')[::-1])) for v in [lv, rv]]
    if ln >= rn: return
    print(f'Updating... {lv} -> {rv}')
    cmd = f'cd {root}; git pull && pip install -e .'
    err = os.system(cmd)
    if err: print(f'Update failed. Please manually update using command:\n{cmd}')
    else: print('Update succeeded')
    return err

def isnew(ss58):
    cd = os.path.dirname(os.path.realpath(__file__))
    last, strat = f'{cd}/../strat/.last-update', f'{cd}/../strat/{ss58}'
    for f in strat, last: ... if os.path.exists(f) else open(f, 'a').close()
    return os.path.getsize(strat) and os.path.getmtime(strat) > os.path.getmtime(last)

def dist(st, nn):
    def fn(x):
        x = [x[k] if k and k in x else 0 for k in nn[asset(x)]]
        s = sum([abs(a) for a in x])
        return [a / s for a in x] if s > 1e-6 else []
    ab = [[] for i in range(len(nn) + 1)]
    for i in range(len(ab) - 1):
        df = st[st['strat'].map(eval).map(asset) == i].copy()
        df['alloc'] = df['strat'].map(eval).map(fn)
        for j, di in df.reset_index().iterrows():
            kk, a, b = di[['uid', 'hotkey']], di['alloc'], di['block']
            ab[i].append([*kk, *df['alloc'].map(lambda x: math.dist(a, x) if a and x else 1)])
            ab[i].append([*kk, *df['block'].map(lambda x: b - x)])
            ab[i][-2][j+2] = 0
    for i in [0, 1]: ab[-1].append([])
    return ab

def dedupe(ab):
    dd = pd.DataFrame([], pd.Index([], name='uid'), ['dedupe'])
    for i in range(len(ab) - 1):
        da = pd.DataFrame(ab[i][0::2], columns=['uid', '', *[*zip(*ab[i])][0][0::2]]).set_index('uid').iloc[:,1:]
        db = pd.DataFrame(ab[i][1::2], columns=['uid', '', *[*zip(*ab[i])][0][1::2]]).set_index('uid').iloc[:,1:]
        print(da.map('{:.4f}'.format).reset_index().to_string(index=False))
        print(db.reset_index().to_string(index=False))
        for uid, di in da.iterrows():
            du = db.loc[uid, di[(di.index != uid) & (di < DD_TRIGGER)].index]
            dd.loc[uid] = min((du[du >= 0].min() / 7200 / DAYS_FINAL) ** DD_POWER, 1)
    for i in [0, 1]:
        print(f"{['black', 'white'][i]}list: {ab[-1][i]}")
        dd.loc[dd.index.isin(ab[-1][i])] = i
    print(dd.dropna().reset_index().to_string(index=False))
    return dd

def score(pl, ab, da, n):
    sim = SimSt()
    sim.pl = pl
    sim.pl2sc()

    sc = sim.sc.join(dedupe(ab), 'uid')
    sc.loc[~sc['dedupe'].isna(), 'score'] *= sc['dedupe']
    sc.insert(7, 'dedupe', sc.pop('dedupe').round(4))

    sc = sc.join(da.set_index('uid')['last'], 'uid')
    dec = (sc['last'] / (sc['days'] + 1)) ** DEC_DECAY
    sc.loc[(dec > DEC_CUTOFF) & (sc['days'] > DAYS_FINAL), 'score'] *= 1 - dec
    sc.insert(4, 'last', sc.pop('last'))

    sim.sc = sc[sc['uid'] < n]
    print(sim.sc2pct().to_string(index=False))
    sc = sim.sc

    score = [sc[sc['uid'] == i]['score'].iat[0] if i in sc['uid'].values else 0 for i in range(n)]
    dec = (sc['last'].sum() / (sc['days'] + 1).sum()) ** DEC_DECAY
    if dec > DEC_CUTOFF: score[DEC_UID] = sum(score) * dec / (1 - dec)
    if not any(score): score[DEC_UID] = 1

    return score, DEC_UID, dec
