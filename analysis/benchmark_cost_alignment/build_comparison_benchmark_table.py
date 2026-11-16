"""Export membership of the plotted non-saturated frontiers from saved results."""
import csv
import json
import math
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = {
    'aa_omniscience': 'AA-Omniscience', 'aa_scicode': 'SciCode (AA)',
    'lech_debate': 'Lech Debate', 'game_arena': 'Strautomata',
    'vals_srebench': 'SREBench (Vals)', 'simplebench': 'SimpleBench',
    'frontiercode': 'FrontierCode', 'bughunt': 'BugHunt',
}
ARENA = {'game_arena', 'lech_debate'}
SCOPE_NOTE = ('Saturation Resistant denotes opponent-relative evaluation, assuming non-solved games '
              'and informative opponent/judge comparisons. No (Individual) denotes no documented '
              'participant-adaptive difficulty mechanism in the evaluated version; it does not mean '
              'the benchmark is already saturated. See comparison_benchmark_saturation_audit.md.')


REPROMPT_NOTE = 'Requires Reprompting asks whether evaluating a new entrant requires fresh inference from previously evaluated participant models. Lech Debate requires selected existing opponents to generate responses in new interactive debates; it does not require every previous model to be called. Fixed individual evaluations can retain previous participants’ scores. Strautomata reuses stored automata without reprompting their originating models. No does not exclude prompting the new entrant, using a separate LLM grader, or rerunning models after a benchmark revision.'

def build():
    memberships = {}
    records = {}
    for view, suffix in [('all', ''), ('top10', '_top10')]:
        with (ROOT / f'alignment_results{suffix}.csv').open() as f:
            rows = list(csv.DictReader(f))
        records[view] = {r['benchmark']: r for r in rows}
        for axis in ['pair_per_unit', 'pair_total']:
            candidates = [r for r in rows if r['saturated'] == 'False'
                          and r[axis] and r['kendall_tau']]
            best = -math.inf
            frontier = set()
            for r in sorted(candidates, key=lambda r: (float(r[axis]), -float(r['kendall_tau']))):
                if float(r['kendall_tau']) > best:
                    best = float(r['kendall_tau'])
                    frontier.add(r['benchmark'])
            memberships[f'{view}_{axis}'] = frontier
    ids = json.loads((ROOT / 'benchmark_ids.json').read_text())
    union = set.union(*memberships.values())
    output = []
    for b in sorted(union, key=lambda b: (2 if b == 'game_arena' else 1 if b == 'lech_debate' else 0, ids[b])):
        row = dict(benchmark_id=ids[b], benchmark=b, name=NAMES.get(b, b))
        row['Saturation Resistant'] = 'Yes (Arena)' if b in ARENA else 'No (Individual)'
        row['Requires Reprompting'] = 'Yes' if b == 'lech_debate' else 'No'
        row.update({key: b in members for key, members in memberships.items()})
        for view in records:
            row[f'{view}_alignment'] = records[view][b]['kendall_tau']
            row[f'{view}_n_overlap'] = records[view][b]['n_overlap']
        output.append(row)
    with (ROOT / 'comparison_benchmark_table.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    lines = ['# Comparison benchmark table', '',
             'Union of benchmarks on the non-saturated Pareto frontier in either panel of the all-model or top-10 view. Membership uses saved point estimates and all eligible costs, before visual axis clipping.', '',
             '| ID | Benchmark | Saturation Resistant | Requires Reprompting | All Pareto ($/unit) | All Pareto (Total $) | K=10 Pareto ($/unit) | K=10 Pareto (Total $) |',
             '|---:|---|---|---|:---:|:---:|:---:|:---:|']
    for row in output:
        label = ('🟢 ' if row['benchmark'] in ARENA else '🔴 ') + row['Saturation Resistant']
        name = '**' + row['name'] + '**' if row['benchmark'] == 'game_arena' else row['name']
        cells = [str(row['benchmark_id']), name, label, row['Requires Reprompting']] + ['✓' if row[k] else '✗' for k in memberships]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', 'SREBench has nine shared models, so its top-10 view uses all nine. “Top 10” selects each benchmark’s highest-consensus available shared models; cohorts can differ. Costs combine Astra and Fable 5.1.']
    (ROOT / 'comparison_benchmark_table.md').write_text('\n'.join(lines) + '\n')
    with (ROOT / 'comparison_benchmark_table.md').open('a') as f:
        f.write('\n' + SCOPE_NOTE + '\n\n' + REPROMPT_NOTE + '\n')
    headers = ['ID', 'Benchmark', 'Saturation Resistant', 'Requires Reprompting', 'All Pareto ($/unit)', 'All Pareto (Total $)', 'K=10 Pareto ($/unit)', 'K=10 Pareto (Total $)']
    html = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Comparison benchmark table</title>',
            '<style>body{font:15px system-ui,sans-serif;color:#26313b;margin:40px}table{border-collapse:collapse}th,td{padding:12px 16px;border-bottom:1px solid #dde3e8;text-align:left}th{background:#f4f6f8}.yes{color:#17843a;font-weight:600}.no{color:#c33535;font-weight:600}.ours td{border-top:3px solid #26313b;font-weight:700}p{max-width:1000px;line-height:1.5}</style>',
            '<h1>Comparison benchmark table</h1><table><thead><tr>' + ''.join('<th>' + escape(h) + '</th>' for h in headers) + '</tr></thead><tbody>']
    for row in output:
        cls = 'yes' if row['benchmark'] in ARENA else 'no'
        reprompt_cls = 'no' if row['benchmark'] == 'lech_debate' else 'yes'
        tr = '<tr class="ours">' if row['benchmark'] == 'game_arena' else '<tr>'
        html.append(tr + '<td>' + str(row['benchmark_id']) + '</td><td>' + escape(row['name']) + '</td><td class="' + cls + '">' + escape(row['Saturation Resistant']) + '</td><td class="' + reprompt_cls + '">' + escape(row['Requires Reprompting']) + '</td>' + ''.join('<td class="' + ('yes' if row[k] else 'no') + '">' + ('✓' if row[k] else '✗') + '</td>' for k in memberships) + '</tr>')
    html += ['</tbody></table><p>Frontier columns exclude observed-saturated benchmarks. SREBench has nine shared models.</p><p>' + escape(SCOPE_NOTE) + '</p><p>' + escape(REPROMPT_NOTE) + '</p></html>']
    (ROOT / 'comparison_benchmark_table.html').write_text('\n'.join(html))
    print('\n'.join(lines))


if __name__ == '__main__':
    build()
