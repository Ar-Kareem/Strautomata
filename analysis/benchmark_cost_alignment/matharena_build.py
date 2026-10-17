import json, re, glob, os, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matharena_parse import parse

HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(',')
SRC = "https://matharena.ai/"
EFFORTS = {'max','xhigh','high','medium','low','minimal','none'}

OVERRIDES = {
 'gpt-6-astra':'gpt-6-astra','alephprover':'aleph-prover','gemini-deep-think-3-12/25':'gemini-deep-think-3','gemini-3.8-flash':'gemini-3.8-flash',
 'nvidia-nemotron-3-super':'nemotron-3-super',
 'qwen3.5-397b-a17b':'qwen-3.5-397b',
 'gemini-3.1-pro-preview':'gemini-3.1-pro','gemini-3-pro-preview':'gemini-3-pro',
 'claude-3.7-sonnet':'claude-sonnet-3.7','claude-3.5-sonnet':'claude-sonnet-3.5',
 'claude-opus-4.0':'claude-opus-4',
 'grok-4.1-fast-reasoning':'grok-4.1-fast','grok-4-fast-r':'grok-4-fast',
 'gpt-oss-120b':'gpt-oss-120b','gpt-oss-20b':'gpt-oss-20b',
 'qwen3-vl-235b-instruct':'qwen-3-vl-235b-instruct',
 'qwen3-235b-2507':'qwen-3-235b-a22b-2507',
 'gemini-2.5-pro-05-06':'gemini-2.5-pro-05-06',
 'deepseek-v3-03-24':'deepseek-v3-0324',
 'gemini-deep-think-3-12/25':'gemini-deep-think-3',
 'gemini-imo-deep-think':'gemini-imo-deep-think',
 'mistral-prover-leanstral-1.5-+-k3':'mistral-prover',
 'grok-4-specific-prompt':'grok-4','gemini-2.5-pro-agent':'gemini-2.5-pro','gemini-2.5-pro-best-of-32':'gemini-2.5-pro',
 'deepseek-v3.2-speciale-agent':'deepseek-v3.2-speciale','gpt-5-agent':'gpt-5',
}

def canon(name):
    """Return (model_canonical, effort, note)."""
    n = name.strip(); note = []
    effort = 'default'
    m = re.search(r'\(([^)]*)\)', n)
    if m:
        inner = m.group(1).strip()
        parts = [p.strip().lower() for p in inner.split(',')]
        if parts[0] in EFFORTS:
            effort = parts[0]; n = n[:m.start()] + n[m.end():]
            if len(parts) > 1: note.append(inner)
        elif parts[0] in ('think','thinking','reasoning'):
            note.append('thinking mode'); n = n[:m.start()] + n[m.end():]
        elif parts[0] in ('preview',):
            n = n[:m.start()] + n[m.end():]; note.append('preview')
        else:
            note.append(inner); n = n[:m.start()] + '-' + inner + n[m.end():]
    n = n.strip()
    # trailing tokens meaning thinking / agent
    if re.search(r'[- ]Think$', n): note.append('thinking mode')
    if n.endswith(' Agent'): note.append('agent'); n = n[:-6]
    c = n.lower().strip()
    c = re.sub(r'\s+', '-', c)
    c = re.sub(r'2507-think$', '2507', c)
    c = re.sub(r'-+', '-', c)
    c = OVERRIDES.get(c, c)
    c = re.sub(r'^(qwen)(\d)', r'\1-\2', c)   # qwen3.5-27b -> qwen-3.5-27b
    c = re.sub(r'-instruct$', '-instruct', c)
    c = re.sub(r'-+', '-', c).strip('-')
    return c, effort, '; '.join(dict.fromkeys(note))

def write(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader(); w.writerows(rows)

# ---- main overall board: IRT "Model analysis across MathArena" (releasePoints in index HTML) ----
pts = json.load(open('raw/matharena_releasePoints.json'))
rows = []
for p in pts:
    c, e, note = canon(p['name'])
    cost = p.get('expected_cost')
    n = ['IRT expected performance across non-deprecated competitions; cost = expected weighted avg per-problem cost', f"slug={p['slug']}", f"release={p.get('release_date')}"]
    if note: n.insert(1, note)
    if cost is None: n.append('no cost published')
    rows.append(dict(benchmark='matharena', model_raw=p['name'], model_canonical=c, effort=e,
                     score=round(p['capability'], 2), cost_usd=round(cost, 4) if cost is not None else '',
                     cost_unit='per_problem', n_tasks='', source_url=SRC, note='; '.join(n)))
write('data/matharena.csv', rows)
astra = next(r for r in rows if r['model_canonical']=='gpt-6-astra')
fab = next(r for r in rows if r['model_canonical']=='claude-fable-5.1')
meta = {"benchmark":"matharena","score_higher_better":True,"cost_unit":"per_problem","n_models":len(rows),
        "astra_cost":astra['cost_usd'],"fable51_cost":fab['cost_usd'],"astra_effort":astra['effort'],"fable51_effort":fab['effort'],
        "fetched":"2026-09-13",
        "how":"matharena.ai index HTML 'Model analysis across MathArena' table (const releasePoints JSON embedded in page): capability = IRT expected % across non-deprecated competitions, expected_cost = weighted avg USD per problem (99 models, 90 with cost). Per-competition tables from GET /competition_tables/<id> written to data/matharena_<id>.csv."}
json.dump(meta, open('data/matharena.meta.json','w'), indent=1)
print('main', len(rows)); print(astra); print(fab)

# ---- per-competition tables ----
for f in sorted(glob.glob('raw/matharena_*.resp')):
    cid = os.path.basename(f)[len('matharena_'):-5]
    hdr, phdr, nprob, trs = parse(f)
    out = []
    for r in trs:
        c, e, note = canon(r['name'])
        n = [f"competition={cid}", f"config={r['config']}"]
        if note: n.insert(0, note)
        if r['predicted']=='yes': n.append('accuracy predicted (not fully evaluated)')
        if r['acc_raw']: n.append('acc_raw=' + r['acc_raw'])
        out.append(dict(benchmark='matharena_'+cid.replace('--','_'), model_raw=r['name'], model_canonical=c, effort=e,
                        score=r['acc'], cost_usd=r['cost'], cost_unit='per_problem', n_tasks=nprob or '',
                        source_url=f"https://matharena.ai/competition_tables/{cid}", note='; '.join(n)))
    write(f"data/matharena_{cid.replace('--','_')}.csv", out)
    print(cid, len(out))
