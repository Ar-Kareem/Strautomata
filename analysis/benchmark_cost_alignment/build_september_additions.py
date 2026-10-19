"""Rebuild two September 14 additions from archived public sources; no network."""
import csv
import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw' / 'september_additions'
FIELDS = 'benchmark model_raw model_canonical effort score cost_usd cost_unit n_tasks source_url note'.split()


def write_board(slug, rows, source, status, evidence, how, extra=None):
    with (ROOT / 'data' / f'{slug}.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(dict(benchmark=slug, **r) for r in rows)
    targets = {r['model_canonical']: r for r in rows}
    a, f = targets['gpt-6-astra'], targets['claude-fable-5.1']
    meta = dict(benchmark=slug, score_higher_better=True, cost_unit=a['cost_unit'],
                n_models=len(targets), n_entries=len(rows), fetched='2026-09-14', how=how,
                astra_cost=a['cost_usd'], fable51_cost=f['cost_usd'],
                astra_effort=a['effort'], fable51_effort=f['effort'],
                cost_audit=dict(status=status, evidence=evidence,
                                source_url=a['source_url'], cached_source=str(source.relative_to(ROOT)),
                                sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    meta.update(extra or {})
    (ROOT / 'data' / f'{slug}.meta.json').write_text(json.dumps(meta, indent=2) + '\n')


def threejs():
    source = RAW / 'threejs_ranking.json'
    data = json.loads(source.read_text())
    rows = []
    for m in data['models']:
        mid = m['modelId']
        match = re.search(r'-(high|medium|low|max)$', mid)
        effort = match[1] if match else 'default'
        canonical = re.sub(r'-(high|medium|low|max)$', '', mid).replace('-thinking', '')
        canonical = canonical.replace('claude-fable-5-1', 'claude-fable-5.1')
        canonical = {'ox-alpha': 'glm-5.3-flash', 'muse-spark-1.3-free': 'muse-spark-1.3'}.get(canonical, canonical)
        rows.append(dict(model_raw=m['label'], model_canonical=canonical, effort=effort,
                         score=m['rating'], cost_usd=m['costUsd'], cost_unit='per_prompt', n_tasks='',
                         source_url='https://threejseval.com/ranking',
                         note=f"Blind pairwise rating; modelId={mid}; battles={m['battles']}; "
                              'costUsd is mean USD per eval (public ranking UI). Vote/prompt counts do not establish '
                              'the number of priced generations. Astra effort unspecified.'))
    write_board('threejs_eval', rows, source, 'count_unverified',
                'Mean generation cost per eval is published; priced generation count is unverified, so no total is inferred from votes or prompt count.',
                'Public /api/ranking JSON: rating and costUsd; archived app labels cost as Mean USD per eval.',
                dict(computed_at=data['computedAt'], api_url='https://threejseval.com/api/ranking',
                     classification='arena (pairwise)'))


def cad():
    source = RAW / 'normal_cad_arena.html'
    soup = BeautifulSoup(source.read_text(), 'html.parser')
    flight = ''.join(json.loads(t.string[len('self.__next_f.push('):-1])[1]
                     for t in soup.find_all('script')
                     if t.string and t.string.startswith('self.__next_f.push([1,'))
    models, _ = json.JSONDecoder().raw_decode(flight.split('"models":', 1)[1])
    identities = {'astra': 'gpt-6-astra', 'fable-5-1': 'claude-fable-5.1',
                  'muse-1-3': 'muse-spark-1.3', 'grok-4-6': 'grok-4.6',
                  'gemini-3-8-flash': 'gemini-3.8-flash',
                  'deepseek-v4': 'deepseek-v4-flash-vision-experimental'}
    rows = []
    for m in models:
        effort = m['reasoning'] if m['reasoning'] != 'No effort setting' else 'default'
        rows.append(dict(model_raw=m['fullName'], model_canonical=identities[m['id']], effort=effort,
                         score=m['score'], cost_usd=m['meanCostUsd'], cost_unit='per_task',
                         n_tasks=m['scored'], source_url='https://normal.ai/leaderboard/cad-arena',
                         note=f"Individual geometry/editability verification; harness={m['harness']}; "
                              f"scored={m['scored']}/{m['scheduled']}; mean cost rounded by source. "
                              '18 parts x 5 platforms; cost excludes unscored trials. Experimental DeepSeek vision variant is not merged with text models.'))
    write_board('normal_cad_arena', rows, source, 'verified_scored_trial_count',
                '18 parts x 5 platforms = 90 scored trials each for Astra and Fable; pair total = (7.13 + 17.70) x 90 = 2234.70 USD, estimated from rounded means.',
                'Next.js page payload models: fullName, reasoning, score, meanCostUsd, scored; leaderboard overall view.',
                dict(classification='individual', run_id='erun_870e9e2d0ad64b7497',
                     source_captured='2026-09-07 20:26 UTC'))


if __name__ == '__main__':
    threejs()
    cad()
