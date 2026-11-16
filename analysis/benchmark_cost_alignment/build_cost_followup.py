"""Rebuild September 14 cost follow-up from archived public data, without network."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw/cost_followup'
FIELDS = 'benchmark model_raw model_canonical effort score cost_usd cost_total_usd cost_unit n_tasks source_url note'.split()


def identity(name):
    name = name.lower().replace(' ', '-').replace('_', '-')
    return re.sub(r'^qwen(\d)', r'qwen-\1', name)


def write(slug, rows, source, **metadata):
    with (ROOT / 'data' / f'{slug}.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(dict(benchmark=slug, **r) for r in rows)
    metadata.update(benchmark=slug, score_higher_better=True, fetched='2026-09-14',
                    n_entries=len(rows), cached_source=str(source.relative_to(ROOT)),
                    sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (ROOT / 'data' / f'{slug}.meta.json').write_text(json.dumps(metadata, indent=2) + '\n')


def duellab():
    source = RAW / 'duellab-leaderboard.json'
    data = json.loads(source.read_text())
    rows = []
    for r in data['rows']:
        if (r['track_id'], r['row_kind'], r['ranking_status']) != ('full_freedom/mixed', 'track', 'ranked'):
            continue
        level = r['reasoning_level'].lower()
        match = re.match(r'^(xhigh|high|medium|low|minimal|max|none)\b', level)
        effort = match[1] if match else 'default'
        c = r['codegen_cost_usd'] or {}
        rows.append(dict(model_raw=r['model_display_name'], model_canonical=identity(r['model_display_name']),
                         effort=effort, score=r['score'], cost_usd=c.get('mean', ''),
                         cost_total_usd=c.get('total', ''), cost_unit='weighted_per_game',
                         n_tasks=c.get('run_count', ''),
                         source_url=f"https://benchmarks.duellab.org/releases/{data['public_release_id']}/leaderboard.json",
                         note=json.dumps(dict(reasoning_level=r['reasoning_level'],
                                              reasoning_provenance=r['reasoning_provenance'],
                                              evaluated_setting_identity=r['evaluated_setting_identity'],
                                              cost_evidence=c,
                                              explanation='Mean equally weights model/game/setting cells; total sums recorded priced runs, including repairs. Do not multiply mean by run_count. Historical effort labels do not establish identical provider settings.'))))
    write('duellab', rows, source, classification='arena (pairwise)', score_kind='normalized_rating',
          public_release_id=data['public_release_id'],
          cost_audit={'status': 'published_mean_and_explicit_total',
                      'evidence': 'Ranked full_freedom/mixed track only; excludes provisional rows. Standard list-price estimates; source excludes infrastructure failures.'})
    return rows


def pinnacle():
    source = RAW / 'pinnacle.html'
    html = source.read_text()
    data, _ = json.JSONDecoder().raw_decode(html.split('var PNC65C_DATA = ', 1)[1])
    rates_text = html.split('var PNC65C_API_PRICES = {', 1)[1].split('\n};', 1)[0]
    rates = {}
    for key, body in re.findall(r'(\w+)\s*:\s*\{([^{}]+)\}', rates_text):
        rates[key] = {k: float(v) for k, v in re.findall(r'\b(inp|out|cache):\s*([\d.]+)', body)}
    rows = []
    for r in data['entities']:
        price = rates.get(r['model'])
        cost = (r['ipc'] * price['inp'] + r['cpo'] * price['out']) / 1e6 if r['api'] else ''
        effort = r['mode'].split(':')[1] if ':' in r['mode'] else ('none' if r['mode'] == 'instruct' else 'default')
        name = identity(r['name'])
        rows.append(dict(model_raw=r['name'], model_canonical=name, effort=effort,
                         score=r['intel'], cost_usd=cost, cost_total_usd='',
                         cost_unit='per_correct_task', n_tasks='', source_url='https://pinnacle.signal65.com/',
                         note=json.dumps(dict(mode=r['mode'], input_estimated=r.get('est'),
                                              input_equivalent_tokens_per_correct=r.get('ipc'),
                                              output_tokens_per_correct=r['cpo'], source_rates=price,
                                              explanation='PINNACLE Model Score pools KAMI and RIKER; component boards not separately imported. Cost includes failed attempts via success normalization; cache discounts already in ipc. Cache-write premiums omitted. Openweight rental costs not imported as API costs. No additive total denominator.'))))
    write('pinnacle', rows, source, classification='individual', score_kind='composite_model_score',
          cost_audit={'status': 'token_derived_per_correct_task_estimate',
                      'evidence': 'Source PNC65C_DATA and PNC65C_API_PRICES. Fable input estimated (est=true); provenance audit not embedded in public page. Total unavailable.'})
    return rows


if __name__ == '__main__':
    duellab()
    pinnacle()
