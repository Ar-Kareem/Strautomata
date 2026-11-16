"""Apply reviewed cost denominators to current data, after running source parsers.

No network access. Evidence hashes prevent silently applying counts to a new
source version. Snapshots are deliberately not modified.
"""
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def decode(value):
    if isinstance(value, list) and len(value) == 2 and value[0] in (0, 1):
        return decode(value[1])
    if isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def vals_tasks(path):
    for component, props in re.findall(r'component-url="([^"]*)"[^>]*props="([^"]*)"', path.read_text()):
        if 'BenchmarkView' in component:
            return decode(json.loads(html.unescape(props)))['benchmarkView']['default']['tasks']
    raise ValueError(f'No benchmark data in {path}')


def component_total(tasks, key, counts):
    values = [tasks[t].get(key, {}).get('cost_per_test') for t in counts]
    if any(v is None for v in values):
        return None
    return sum(float(v) * n for v, n in zip(values, counts.values()))


def enrich():
    manifest = json.loads((ROOT / 'cost_count_sources.json').read_text())
    for bench, spec in manifest['benchmarks'].items():
        source = ROOT / spec['source_file'] if spec.get('source_file') else None
        if source and hashlib.sha256(source.read_bytes()).hexdigest() != spec['source_sha256']:
            raise ValueError(f'{bench}: source changed; re-review cost_count_sources.json')
        for evidence in spec.get('additional_evidence_files', []):
            if hashlib.sha256((ROOT / evidence['path']).read_bytes()).hexdigest() != evidence['sha256']:
                raise ValueError(f'{bench}: additional source changed; re-review counts')
        path = ROOT / 'data' / f'{bench}.csv'
        with path.open(newline='') as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        if 'cost_total_usd' not in fields:
            fields.append('cost_total_usd')
        tasks = vals_tasks(source) if spec['status'] == 'component_sum' else None
        pairs = {}
        if spec['status'] == 'row_count':
            for line in source.read_text().splitlines():
                parts = [s.strip() for s in line.strip('|').split('|')]
                if len(parts) == 10 and parts[0].isdigit():
                    pairs[parts[1]] = (float(parts[2]), int(parts[7]))
        for row in rows:
            row['cost_total_usd'] = ''
            row['n_tasks'] = ''
            status = spec['status']
            if status in ('verified_count', 'component_sum'):
                row['n_tasks'] = str(spec['n_tasks'])
            if status == 'component_sum':
                key = re.search(r'(?:^|; )model_key=([^;]+)', row['note']).group(1)
                total = component_total(tasks, key, spec['components'])
                row['cost_total_usd'] = '' if total is None else f'{total:.6f}'
                # The original cost is a repository-weighted mean, not an
                # execution mean; retain it rather than silently changing x.
                row['cost_unit'] = 'weighted_per_test'
            elif status == 'row_count':
                score, count = pairs[row['model_raw']]
                if abs(score - float(row['score'])) > 0.001:
                    raise ValueError(f'{bench}: rating/count snapshot mismatch')
                row['n_tasks'] = str(2 * count)
            row['note'] = re.sub(r'; cost audit:.*$', '', row['note'])
            row['note'] += f"; cost audit: {status}; see cost_count_sources.json"
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        mp = path.with_suffix('.meta.json')
        meta = json.loads(mp.read_text())
        meta['cost_audit'] = dict(spec, reviewed=manifest['reviewed'])
        if spec['status'] == 'component_sum':
            meta['cost_unit'] = 'weighted_per_test'
        # Remove the parser's obsolete blanket claim.
        meta['how'] = meta['how'].replace('; n_tasks not published.', '; see cost_audit for denominator evidence.')
        mp.write_text(json.dumps(meta, indent=1) + '\n')
        print(f"{bench}: {spec['status']}, n={spec.get('n_tasks', 'row-specific / unresolved')}")


if __name__ == '__main__':
    enrich()
