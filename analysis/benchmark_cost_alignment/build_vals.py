"""Build data/vals_<slug>.csv + .meta.json for every Vals AI benchmark page under raw/vals_benchmarks/.
Numbers come from the Astro island props (component BenchmarkView, key benchmarkView.default.tasks.<task>),
model labels/effort from the model registry embedded in raw/vals_constants.BzMCAmxE.js (parsed to raw/vals_model_registry.json)."""
import re, json, html, glob, os, csv, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.abspath(__file__))
FETCHED = "2026-09-13"

def dec(x):
    if isinstance(x, list) and len(x) == 2 and isinstance(x[0], int) and x[0] in (0, 1) and (x[0] == 1 and isinstance(x[1], list) or x[0] == 0):
        if x[0] == 0:
            return dec(x[1]) if isinstance(x[1], (dict, list)) else x[1]
        return [dec(i) for i in x[1]]
    if isinstance(x, dict): return {k: dec(v) for k, v in x.items()}
    if isinstance(x, list): return [dec(i) for i in x]
    return x

def islands(path):
    s = open(path).read()
    out = []
    for m in re.finditer(r'component-url="([^"]*)"[^>]*props="([^"]*)"', s):
        try: out.append((m.group(1), dec(json.loads(html.unescape(m.group(2))))))
        except Exception: pass
    return out

# ---------- model registry ----------
def parse_registry():
    s = open(os.path.join(ROOT, 'raw/vals_constants.BzMCAmxE.js')).read()
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'"([a-z0-9_-]+/[^"]+)":\{company:"', s)]
    reg = {}
    for i, (pos, key) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(s)
        body = s[pos:end]
        label = re.search(r'label:"([^"]*)"', body).group(1)
        company = re.search(r'company:"([^"]*)"', body).group(1)
        slug = re.search(r'slug:"([^"]*)"', body)
        harness = re.search(r'agent_harness:"([^"]*)"', body)
        rm = re.search(r'reasoning_model:(!0|!1)', body)
        pre = body.split('provider_endpoint:')[0]
        dps = re.findall(r'default_parameters:\{([^}]*)\}', pre)
        params = dict(re.findall(r'(\w+):("?[^,"]*"?)', dps[-1])) if dps else {}
        alts = {}
        if 'alternative_keys:[{' in body:
            altsec = body.split('alternative_keys:[')[1]
            for am in re.finditer(r'\{"([^"]+)":\{label:"([^"]*)"(.*?)\}\}', altsec.split(']')[0] + ']'):
                ap = dict(re.findall(r'(\w+):("?[^,"{}]*"?)', am.group(3)))
                alts[am.group(1)] = {'label': am.group(2), 'params': ap}
        reg[key] = {'label': label, 'slug': slug.group(1) if slug else None, 'company': company,
                    'params': params, 'alts': alts, 'harness': harness.group(1) if harness else None,
                    'reasoning_model': (rm.group(1) == '!0') if rm else None}
    return reg

REG = parse_registry()
json.dump(REG, open(os.path.join(ROOT, 'raw/vals_model_registry.json'), 'w'), indent=1)
ALT = {ak: (pk, av) for pk, r in REG.items() for ak, av in r['alts'].items()}

def lookup(key):
    """-> (label, effort_raw, slug, harness, note)"""
    if key in REG:
        r = REG[key]; p = r['params']
    elif key in ALT:
        pk, av = ALT[key]; r = REG[pk]; p = dict(r['params']); p.update(av['params'])
        return av['label'], effort_of(p), r['slug'], r['harness'], 'alternative key of ' + pk
    else:
        return key.split('/', 1)[-1], None, None, None, 'model key not in registry'
    return r['label'], (effort_of(p) if r['reasoning_model'] is not False else None), r['slug'], r['harness'], ''

def effort_of(p):
    for k in ('compute_effort', 'reasoning_effort', 'thinking_level'):
        if k in p and p[k] not in ('null', ''):
            return p[k].strip('"')
    return None

EFFORT_MAP = {'default': 'default', 'none': 'none', 'minimal': 'minimal', 'low': 'low', 'medium': 'medium', 'high': 'high', 'xhigh': 'xhigh', 'max': 'max'}

# effort/canonical already verified for the 56 index models (from model pages) -> reuse
INDEX = {}
with open(os.path.join(ROOT, 'data/vals_index.csv')) as f:
    for row in csv.DictReader(f):
        INDEX[row['source_url'].rsplit('/', 1)[-1]] = row  # keyed by slug

def canonical(label):
    x = label.lower().replace('(non-reasoning)', 'non-reasoning')
    x = re.sub(r'\((thinking|reasoning|high|low|medium|max|xhigh|extra high effort|high effort|medium effort|low effort|no fallback|non-reasoning|\d\d/\d\d)\)', '', x)
    x = re.sub(r'\b(preview|latest)\b', '', x)
    x = x.replace('gpt ', 'gpt-')
    x = re.sub(r'\b(qwen|glm|grok|kimi|mimo|llama|gemma|mistral|magistral|jamba|nemotron|minimax|deepseek)(\d)', r'\1-\2', x)
    x = re.sub(r'[^a-z0-9.]+', '-', x).strip('-')
    x = re.sub(r'-+', '-', x)
    return x

def build(path):
    slug = os.path.basename(path)[:-5]
    bench = 'vals_' + slug.replace('-', '_')
    view = None
    for url, p in islands(path):
        if 'BenchmarkView' in url and 'benchmarkView' in p:
            view = p; break
    if view is None:
        print('SKIP (no BenchmarkView island)', slug); return None
    bv = view['benchmarkView']; md = bv['metadata']; tasks = bv['default']['tasks']
    task = view.get('defaultTask') if isinstance(view.get('defaultTask'), str) and view.get('defaultTask') in tasks else 'overall'
    rows = tasks[task]
    url = f'https://www.vals.ai/benchmarks/{slug}'
    out = []
    for key, r in rows.items():
        if r.get('accuracy') is None: continue
        label, eff_raw, mslug, harness, note = lookup(key)
        note_parts = [f'model_key={key}']
        # per-row hyperparameters published on the benchmark page take precedence over registry defaults
        row_eff = None
        for ek in ('compute_effort', 'reasoning_effort'):
            if r.get(ek) not in (None, ''): row_eff = str(r[ek]); break
        if row_eff is None and r.get('reasoning') is not None: note_parts.append(f'reasoning={r["reasoning"]}')
        if mslug in INDEX and 'alternative key' not in note:
            ix = INDEX[mslug]; canon = ix['model_canonical']
            if ix['model_raw'] != label: label = ix['model_raw']
            eff_src = row_eff if row_eff is not None else ix['effort']
        else:
            canon = canonical(label); eff_src = row_eff if row_eff is not None else eff_raw
        effort = EFFORT_MAP.get(eff_src or '', 'default')
        if eff_src and eff_src not in EFFORT_MAP: note_parts.append(f'effort_raw={eff_src}')
        if row_eff is None and effort != 'default': note_parts.append('effort from model registry default (not shown per-row)')
        if harness: note_parts.append(f'agent harness: {harness}')
        if r.get('harness'): note_parts.append(f'harness={r["harness"]}')
        if r.get('latency') is not None: note_parts.append(f'latency_s={r["latency"]}')
        if task != 'overall': note_parts.append(f'task={task}')
        if note: note_parts.append(note)
        cost = r.get('cost_per_test')
        out.append({'benchmark': bench, 'model_raw': label, 'model_canonical': canon, 'effort': effort,
                    'score': r['accuracy'], 'cost_usd': '' if cost is None else cost,
                    'cost_unit': '' if cost is None else 'per_test', 'n_tasks': '', 'source_url': url,
                    'note': '; '.join(note_parts)})
    out.sort(key=lambda d: -float(d['score']))
    if len(out) < 8:
        print(f'SKIP {slug}: only {len(out)} models'); return None
    with open(os.path.join(ROOT, f'data/{bench}.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['benchmark', 'model_raw', 'model_canonical', 'effort', 'score', 'cost_usd', 'cost_unit', 'n_tasks', 'source_url', 'note'])
        w.writeheader(); w.writerows(out)
    def find(c):
        for d in out:
            if d['model_canonical'] == c and 'alternative key' not in d['note']: return d
    a, fb = find('gpt-6-astra'), find('claude-fable-5.1')
    ncost = sum(1 for d in out if d['cost_usd'] != '')
    meta = {'benchmark': bench, 'score_higher_better': True, 'cost_unit': 'per_test' if ncost else None,
            'n_models': len(out), 'n_models_with_cost': ncost,
            'astra_cost': (a['cost_usd'] if a and a['cost_usd'] != '' else None), 'fable51_cost': (fb['cost_usd'] if fb and fb['cost_usd'] != '' else None),
            'astra_effort': a['effort'] if a else None, 'fable51_effort': fb['effort'] if fb else None,
            'astra_score': a['score'] if a else None, 'fable51_score': fb['score'] if fb else None,
            'fetched': FETCHED, 'site_name': md['benchmark'], 'site_version': md['version'], 'site_updated': md['updated'],
            'mode': md.get('mode'), 'use_cost_per_test_flag': md.get('use_cost_per_test'), 'task': task,
            'note': ('leaf page overall differs from the code_migration component shown on /benchmarks/vals_index for the same models (index uses a different aggregation of the same run; costs match)' if slug == 'code-migration' else ''),
            'vals_index_component': slug in ('fabv2', 'emb', 'terminal-bench-2-1', 'vibe-code', 'code-migration', 'legal_research', 'hlab'),
            'how': f"{url} Astro island BenchmarkView props (html-escaped JSON) -> benchmarkView.default.tasks.{task}[model_key] = {{accuracy, latency, cost_per_test}}; effort = per-row compute_effort|reasoning_effort from the same props (fallback: model registry default_parameters in /_astro/constants.BzMCAmxE.js, then data/vals_index.csv); labels from that registry. score = accuracy (%), cost = mean $ per test; n_tasks not published."}
    json.dump(meta, open(os.path.join(ROOT, f'data/{bench}.meta.json'), 'w'), indent=1)
    return bench, len(out), ncost, a, fb

if __name__ == '__main__':
    res = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'raw/vals_benchmarks/*.html'))):
        if p.endswith('vals_index.html'): continue
        r = build(p)
        if r: res.append(r)
    print(f'{"bench":32} {"n":>4} {"ncost":>5}  astra(score,cost,eff) | fable51(score,cost,eff)')
    for b, n, nc, a, fb in res:
        fa = f"{a['score']},{a['cost_usd']},{a['effort']}" if a else '-'
        ff = f"{fb['score']},{fb['cost_usd']},{fb['effort']}" if fb else '-'
        print(f'{b:32} {n:4} {nc:5}  {fa} | {ff}')
