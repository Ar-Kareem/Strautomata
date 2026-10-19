"""Generate iter/bt × clean/all live-play figures. See README.txt."""
from pathlib import Path
import argparse,copy,json,sys,hashlib
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import numpy as np
import pandas as pd
from game_arena import run_leaderboard
from game_arena.utils import get_match_result
from experimental.lm_arena import simple_example
from experimental.exp_utils import get_match_file_path,get_match_results
from render import render
OUT=Path(__file__).resolve().parent
GAMES=[('connect4','world1','Connect4'),('chess','worlduci1','Chess UCI')]

def classify(d):
    if d.get('done'):return 'completed',None
    err=d.get('player_err_counts',[])
    if len(err)!=2 or sorted(err)!=[0,1]:return 'unattributed_failure',None
    loser=err.index(1)
    ex=str(d.get('exception',''))
    tb=str(d.get('exception_traceback',''))
    # Terminal API errors take precedence over earlier illegal retries.
    if 'No response from' in tb or 'failed API calls' in ex or '[Errno' in ex:
        return 'api_or_harness_failure',None
    if ex.startswith(('Invalid move_str:','Invalid or illegal move:')) or 'all illegal moves' in ex:
        return 'illegal_move',loser
    if ex.startswith('Max retry count') and 'reached for move:' in tb:
        return 'illegal_move',loser
    if ex.startswith('Policy raised an exception:'):
        # Require the fault to belong to an automaton, not API work inside an LLM.
        if not d[f'name{loser}'].startswith('LLM_'):return 'bot_code_error',loser
    return 'unknown_failure',None

def normalize(d,kind,loser):
    d=copy.deepcopy(d)
    if kind!='completed':
        d['winner']='error';d['r']={k:d.get(k) for k in ('player_err_counts','done','move_count','exception')}
    else:d['r']={'player_err_counts':d.get('player_err_counts',[0,0])}
    if d.get('live_play',{}).get('show_legal_moves',False):
        k='name0' if d['name0'].startswith('LLM_') else 'name1'
        d[k]='LLM_PEEK_'+d[k][4:]
    return d

def load():
    records={title:[] for _,_,title in GAMES};audit=[];seen=set()
    for folder in ['results_live_legacy_pre_2026_oct','results_live']:
        for game,world,title in GAMES:
            for fp in sorted((ROOT/'results_side_experiments'/folder).glob(f'*/{game}_{world}/*.json')):
                if fp.parent.parent.name=='trash':continue
                d=json.loads(fp.read_text());digest=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
                kind,loser=classify(d)
                if digest in seen:kind='duplicate';loser=None
                seen.add(digest)
                row=dict(path=str(fp.relative_to(ROOT)),game=title,source=folder,classification=kind,loser=d.get(f'name{loser}') if loser is not None else '',clean=kind=='completed',all=kind in ['completed','illegal_move'] or (args.bot_errors=='include' and kind=='bot_code_error'))
                audit.append(row)
                if row['all']:records[title].append((normalize(d,kind,loser),kind))
    if args.export_data:pd.DataFrame(audit).to_csv(OUT/'game_audit.csv',index=False)
    return records

def make_pairs(base,live):
    rows=[]
    for name,value in base.items():
        if not name.startswith('LLM_'):continue
        model=name.removeprefix('LLM_').removeprefix('PEEK_')
        if model not in base.index:continue
        scores=[]
        for m in live:
            if name not in (m['name0'],m['name1']):continue
            reason,w=get_match_result(m,False);i=0 if m['name0']==name else 1
            scores.append(.5 if reason=='draw' else float(w==i))
        rows.append(dict(model=model,live_name=name,Automaton=base[model],**{'Live Play':value},finite=any(s>0 for s in scores) and any(s<1 for s in scores),games=len(scores),wins=scores.count(1),losses=scores.count(0),draws=scores.count(.5)))
    return pd.DataFrame(rows).set_index('model')

def main():
    records=load();frames={(method,variant):[] for method in ['iter','bt'] for variant in ['clean','all']}
    for game,world,title in GAMES:
        raw=get_match_results(get_match_file_path(game,world,result_dir=str(ROOT/'results_current/results_somerset_feb_20/tourney')))
        _,iter_top=run_leaderboard.get_elo_df_combined(copy.deepcopy(raw),combine_method='top_1',verbose=False)
        iter_top=set(iter_top)
        iter_auto=[m for m in raw if m['name0'] in iter_top and m['name1'] in iter_top and not any('OLD_' in m[k] for k in ('name0','name1'))]
        tourney,ts=simple_example.get_match_results(game,world,None,'results_current/results_somerset_feb_20/tourney')
        bt_top=simple_example.get_top_bot_per_model(copy.deepcopy(tourney),'bt',n=1)
        for variant in ['clean','all']:
            live=[copy.deepcopy(m) for m,kind in records[title] if variant=='all' or kind=='completed']
            for method in ['iter','bt']:
                dest=OUT/method/variant;dest.mkdir(parents=True,exist_ok=True)
                if method=='iter':
                    matches=copy.deepcopy(iter_auto)+copy.deepcopy(live)
                    for m in matches:
                        for k in ('name0','name1'):m[k]=m[k].split('/')[0]
                    ratings,_=run_leaderboard.get_elo_df_combined(matches,combine_method='none',verbose=False,learning_rate=2)
                    base=ratings.ELO
                else:
                    np.random.seed(42)
                    result=simple_example.main_results(copy.deepcopy(tourney)+copy.deepcopy(live),ts,rating_system='bt',num_bootstrap=100,num_cpu=4,only_model=False)
                    ratings=result['leaderboard_table_df']
                    if args.export_data:ratings.to_csv(dest/f'{game}_bot_ratings.csv')
                    values={n.split('/')[0]:float(ratings.at[n,'rating']) for n in bt_top if n in ratings.index}
                    values.update({n:float(ratings.at[n,'rating']) for n in ratings.index if n.startswith('LLM_')})
                    base=pd.Series(values)
                if args.export_data:base.to_csv(dest/f'{game}_ratings.csv')
                base=base.drop(index=['claude_sonnet_4','gemini_2.5_flash'],errors='ignore')
                pairs=make_pairs(base,live);pairs.insert(0,'game',title);frames[method,variant].append(pairs)
                print(method,variant,title,'live games',len(live),'pairs',len(pairs),flush=True)
    for (method,variant),parts in frames.items():
        points=pd.concat(parts);dest=OUT/method/variant
        if args.export_data:points.to_csv(dest/'plot_points.csv')
        for style in ['numbers','hand']:render(points,method,variant,style,dest)
    (OUT/'settings.json').write_text(json.dumps({'bot_errors':args.bot_errors,'sources':['results_live_legacy_pre_2026_oct','results_live'],'tournament':'results_current/results_somerset_feb_20/tourney','clean':'completed only','all':'completed + terminal illegal moves'+(' + attributable bot-code errors' if args.bot_errors=='include' else ''),'bt':'simple_example.main_results, rating_system=bt, only_model=False; best tournament bot per parent','iter':'notebook top1 selection and parent collapse; 20 passes, final learning_rate=2'},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bot-errors',choices=['include','exclude'],default='include');parser.add_argument('--export-data',action='store_true');args=parser.parse_args();main()
