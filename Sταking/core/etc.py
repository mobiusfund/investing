# Copyright © 2025 Mobius Fund

import os, requests
from .const import RAWGIT_ROOT
from .simst import SimSt

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

def issimilar():
    pass

def score(pl, n):
    sim = SimSt()
    sim.pl = pl
    sim.pl2sc()
    sc = sim.sc
    sim.sc = sc[sc['uid'] < n]
    print(sim.sc2pct().to_string(index=False))
    sc = sim.sc
    score = [sc[sc['uid'] == i]['score'].iat[0] if i in sc['uid'].values else 0 for i in range(n)]
    return score
