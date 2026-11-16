import json, re, csv, collections
EFFORTS = {'max':'max','xhigh':'xhigh','high':'high','medium':'medium','low':'low','minimal':'minimal','none':'none'}
# modelId -> canonical (effort-free). Anything not listed is derived by rule.
CANON = {
 '2025_human_panel':'human-panel','mturker':'human-mturker','stem_grad':'human-stem-grad',
 'ARChitects':'architects-2024','Icecuber':'icecuber-2020','NVARC_2025':'nvarc-2025',
 'Claude 3.7':'claude-sonnet-3.7','Claude 3.7 Thinking':'claude-sonnet-3.7',
 'Gemini 1.5 Pro':'gemini-1.5-pro','Gemini 2.0 Flash':'gemini-2-flash',
 'Llama-4-Maverick-17B-128E-Instruct-FP8-together':'llama-4-maverick','Llama-4-Scout-17B-16E-Instruct-together':'llama-4-scout',
 'R1':'deepseek-r1','deepseek_r1_0528-openrouter':'deepseek-r1-0528','deepseek-v3.2':'deepseek-v3.2',
 'anthropic-claude-fable-5-1':'claude-fable-5.1','anthropic-claude-fable-5':'claude-fable-5','anthropic-claude-opus-5':'claude-opus-5',
 'anthropic-opus-4-8':'claude-opus-4.8','claude-4-7':'claude-4.7','claude-haiku-4-5-20251001':'claude-haiku-4.5',
 'claude-opus-4-20250514':'claude-opus-4','claude-opus-4-5-20251101':'claude-opus-4.5','claude-opus-4-6-thinking-120K':'claude-opus-4.6',
 'claude-sonnet-4-20250514':'claude-sonnet-4','claude-sonnet-4-5-20250929':'claude-sonnet-4.5','claude_sonnet_4_6':'claude-sonnet-4.6',
 'codex-mini-latest':'codex-mini','deepseek-v4-flash-0731':'deepseek-v4-flash','deepseek-v4-pro-0813':'deepseek-v4-pro',
 'eric_pang_sept_2025':'grok-4-refinement-pang','jeremy_sept_2025':'grok-4-refinement-berman','johan_land_gpt_5_2_refine':'gpt-5.2-refinement-land',
 'poetiq-arc-agi-gemini-3-d_v1':'gemini-3-pro-refinement-poetiq',
 'gemini-2-5-flash-preview-05-20':'gemini-2.5-flash','gemini-2-5-pro-2025-06-17':'gemini-2.5-pro','gemini-2-5-pro-preview-05-06':'gemini-2.5-pro-preview',
 'gemini-2-5-pro-preview-openrouter':'gemini-2.5-pro-preview','gemini-3-1-pro-preview':'gemini-3.1-pro','gemini-3-5-flash':'gemini-3.5-flash',
 'gemini-3-5-flash-lite':'gemini-3.5-flash-lite','gemini-3-6-flash':'gemini-3.6-flash','gemini-3-deep-think-preview':'gemini-3-deep-think',
 'gemini_3_deep_think_022026':'gemini-3-deep-think-0226','gemini-3-flash-preview-thinking':'gemini-3-flash','gemini-3-pro-preview':'gemini-3-pro',
 'glm-5':'glm-5','glm-5.2':'glm-5.2','google-gemini-3-7-flash':'gemini-3.7-flash',
 'gpt-4-1-2025-04-14':'gpt-4.1','gpt-4-1-mini-2025-04-14':'gpt-4.1-mini','gpt-4-1-nano-2025-04-14':'gpt-4.1-nano','gpt-4-5-2025-02-27':'gpt-4.5',
 'gpt-4o-2024-11-20':'gpt-4o','gpt-4o-mini-2024-07-18':'gpt-4o-mini',
 'gpt-5-1-2025-11-13-thinking':'gpt-5.1','gpt-5-2-2025-12-11-thinking':'gpt-5.2','gpt-5-2-pro-2025-12-11':'gpt-5.2-pro','gpt-5-2025-08-07':'gpt-5',
 'gpt-5-4':'gpt-5.4','gpt-5-4-mini':'gpt-5.4-mini','gpt-5-4-nano':'gpt-5.4-nano','gpt-5-4-pro':'gpt-5.4-pro',
 'gpt-5-5-2026-04-22-thinking':'gpt-5.5','gpt-5-5-pro-2026-04-23':'gpt-5.5-pro','gpt-5-mini-2025-08-07':'gpt-5-mini','gpt-5-nano-2025-08-07':'gpt-5-nano',
 'gpt-5-pro-2025-10-06':'gpt-5-pro','gpt-5-1-2025-11-13':'gpt-5.1','gpt-5-2-2025-12-11':'gpt-5.2',
 'anthropic-opus-4-6':'claude-opus-4.6','xai-grok-4-20-beta-0309-reasoning':'grok-4.20','openai-gpt-5-4-2026-03-05':'gpt-5.4',
 'google-gemini-3-1-pro-preview':'gemini-3.1-pro','openai-gpt-5-5-2026-04-23':'gpt-5.5','anthropic-opus-4-7':'claude-opus-4.7',
 'grok-3-mini-beta-low-openrouter':'grok-3-mini','grok-3-openrouter':'grok-3','grok-4-0709':'grok-4','grok-4-fast-reasoning':'grok-4-fast',
 'grok-4.20-beta-0309b-reasoning':'grok-4.20','xai-grok-4-5':'grok-4.5','xai-grok-4-6':'grok-4.6',
 'hrm-2-2508':'hrm','trm-2025-10-07':'trm','kimi-k2.5':'kimi-k2.5','moonshot-kimi-k3':'kimi-k3',
 'magistral-medium-2506':'magistral-medium','magistral-medium-2506-thinking':'magistral-medium','magistral-small-2506':'magistral-small',
 'minimax-m2.5':'minimax-m2.5','o1-mini-2024-09-12':'o1-mini','o3-2025-04-16':'o3','o3-mini-2025-01-31':'o3-mini','o3-preview':'o3-preview',
 'o3-pro-2025-06-10':'o3-pro','o4-mini-2025-04-16':'o4-mini',
 'openai-gpt-5-6-luna':'gpt-5.6-luna','openai-gpt-5-6-luna-2026-07-30':'gpt-5.6-luna-2026-07-30','openai-gpt-5-6-sol':'gpt-5.6-sol',
 'openai-gpt-5-6-terra':'gpt-5.6-terra','openai-gpt-6-astra':'gpt-6-astra',
 'qwen3-235b-a22b-instruct-2507':'qwen-3-235b-a22b-instruct','thinky-inkling':'inkling','thinky-inkling-small':'inkling-small',
}
def parse(mid, disp):
    """return (base_id, effort, note)"""
    note=''
    # thinking budgets
    m = re.match(r'^(.*?)-thinking-(\d+k|none)(-bedrock)?$', mid, re.I)
    if m:
        base=m.group(1); b=m.group(2).lower()
        if b=='none': return base,'none',''
        return base,'default',f'thinking budget {b.upper()}'
    m = re.match(r'^Claude 3\.7 Thinking (\d+K)$', mid)
    if m: return 'Claude 3.7 Thinking','default',f'thinking budget {m.group(1)}'
    # trailing effort, optionally followed by date (luna 2026-07-30)
    m = re.match(r'^(.*?)[-_](max|xhigh|high|medium|low|minimal|none)(-\d{4}-\d{2}-\d{2})?$', mid)
    if m:
        base=m.group(1)+(m.group(3) or '')
        return base, m.group(2), ''
    # effort-like text in display name only
    m = re.search(r'\((?:.*?,\s*)?(Max|XHigh|High|Medium|Low|Minimal|None)\)', disp)
    if m and mid!='gpt-5-2-2025-12-11-thinking-none':
        return mid, m.group(1).lower(), ''
    return mid,'default',''
rows_all={}
for v,bench,ntasks in [('v1','arc_agi_1',100),('v2','arc_agi_2',120),('v3','arc_agi_3',None)]:
    d=json.load(open(f'raw/arc_lb_{v}.json'))
    out=[]
    for e in d['evaluations']:
        mid=e['modelId']; disp=e['modelDisplayName']
        pid=re.sub(r'-provider-adapter$','',mid); pid=re.sub(r'-effort$','',pid)
        base,eff,note=parse(pid,disp)
        if v=='v3':
            base=re.sub(r'-effort$','',base); base=re.sub(r'-provider-adapter$','',base)
        canon=CANON.get(base)
        if canon is None:
            canon=base.lower().replace('_','-'); note=(note+'; ' if note else '')+'canonical auto-derived'
        notes=[note] if note else []
        if 'provider-adapter' in mid or 'Provider Adapter' in disp: notes.append('provider adapter')
        if not e.get('display',True): notes.append('display=false in source (hidden on chart)')
        if e.get('modelType')=='Refinement': notes.append('refinement harness on top of model')
        if e.get('modelType')=='Custom' or e['providerDisplayName'].startswith('ARC Prize'): notes.append('Kaggle competition solution')
        if e['providerDisplayName']=='Human': notes.append('human baseline')
        if mid=='grok-3-mini-beta-low-openrouter': eff='low'
        if mid=='gpt-5-2-2025-12-11-thinking-none': eff='none'
        cost = e.get('costPerTask', e.get('cost'))
        unit = 'per_task' if 'costPerTask' in e else 'total_run'
        out.append(dict(benchmark=bench, model_raw=disp, model_canonical=canon, effort=eff,
            score=round(e['score']*100,4) if e['score'] is not None else '',
            cost_usd=round(cost,6) if cost is not None else '', cost_unit=unit, n_tasks=ntasks or '',
            source_url='https://arcprize.org/leaderboard'+(('#'+e['resultsUrl']) if e['resultsUrl'] else ''),
            note='; '.join(notes)))
    # duplicate detection
    c=collections.Counter(e['modelId'] for e in d['evaluations'])
    for r,e in zip(out,d['evaluations']):
        if c[e['modelId']]>1: r['note']=(r['note']+'; ' if r['note'] else '')+'duplicate entry in source data'
    with open(f'data/{bench}.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames='benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note'.split(','))
        w.writeheader(); w.writerows(out)
    def pick(canon,eff):
        r=[x for x in out if x['model_canonical']==canon and x['effort']==eff and 'provider adapter' not in x['note']]
        return r[0] if r else None
    a=pick('gpt-6-astra','high'); fb=pick('claude-fable-5.1','high')
    meta={"benchmark":bench,"score_higher_better":True,"cost_unit":out[0]['cost_unit'],"n_models":len(out),
          "astra_cost":a['cost_usd'] if a else None,"fable51_cost":fb['cost_usd'] if fb else None,
          "astra_effort":"high" if a else None,"fable51_effort":"high" if fb else None,"fetched":"2026-09-13",
          "how":f"https://arcprize.org/media/data/leaderboard/{v}.json (evaluations[] with datasetId={v}_Semi_Private; loaded by /scripts/leaderboard/data.js on /leaderboard); score fraction*100, cost=costPerTask USD"}
    if v=='v3': meta['how']=meta['how'].replace('cost=costPerTask USD','cost=total run cost USD (no per-task cost published)')
    json.dump(meta,open(f'data/{bench}.meta.json','w'),indent=1)
    print(bench,len(out),'rows; auto-derived:',sum('auto-derived' in r['note'] for r in out))
    for r in out:
        if r['model_canonical'] in ('gpt-6-astra','claude-fable-5.1'): print('  ',','.join(str(r[k]) for k in r))
