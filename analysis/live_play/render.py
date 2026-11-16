"""Shared styling and consistent model IDs for every live-play comparison."""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.transforms import Bbox
SELECTED={'gpt_4o_mini','gemini_3_flash_preview','ministral_14b_2512','gpt_5_mini','qwen3_235b_a22b_2507','deepseek_v3.2'}

MODEL_KEY = [{'number': '1', 'model': 'deepseek_chat_v3_0324', 'label': 'DeepSeek V3 0324'}, {'number': '2', 'model': 'deepseek_v3.2', 'label': 'DeepSeek V3.2'}, {'number': '3', 'model': 'devstral_2512_free', 'label': 'Devstral 2512'}, {'number': '4', 'model': 'gemini_2.0_flash_001', 'label': 'Gemini 2.0 Flash'}, {'number': '5', 'model': 'gemini_3_flash_preview', 'label': 'Gemini 3 Flash Preview'}, {'number': '6', 'model': 'gpt_4o_mini', 'label': 'GPT-4o Mini'}, {'number': '7', 'model': 'gpt_5_mini', 'label': 'GPT-5 Mini'}, {'number': '8', 'model': 'gpt_oss_120b', 'label': 'GPT-OSS 120B'}, {'number': '9', 'model': 'grok_code_fast_1', 'label': 'Grok Code Fast 1'}, {'number': '10', 'model': 'kat_coder_pro', 'label': 'KAT Coder Pro'}, {'number': '11', 'model': 'kimi_k2_thinking', 'label': 'Kimi K2 Thinking'}, {'number': '12', 'model': 'minimax_m2', 'label': 'MiniMax M2'}, {'number': '13', 'model': 'minimax_m2.1', 'label': 'MiniMax M2.1'}, {'number': '14', 'model': 'ministral_14b_2512', 'label': 'Ministral 14B 2512'}, {'number': '15', 'model': 'nemotron_nano_12b_v2_vl_free', 'label': 'Nemotron Nano 12B V2 VL'}, {'number': '16', 'model': 'qwen3_235b_a22b_2507', 'label': 'Qwen3 235B A22B 2507'}, {'number': '17', 'model': 'qwen3_32b', 'label': 'Qwen3 32B'}, {'number': '18', 'model': 'qwen3_coder', 'label': 'Qwen3 Coder'}, {'number': '19', 'model': 'qwen3_coder_30b_a3b_instruct', 'label': 'Qwen3 Coder 30B A3B'}, {'number': '20', 'model': 'qwen3_next_80b_a3b_instruct', 'label': 'Qwen3 Next 80B A3B'}, {'number': '21', 'model': 'tng_r1t_chimera_free', 'label': 'TNG R1T Chimera'}, {'number': '22', 'model': 'trinity_mini_free', 'label': 'Trinity Mini'}]

def render(points,method,variant,style,dest):
    key=pd.DataFrame(MODEL_KEY);names=key.model.tolist();numbers=dict(zip(key.model,key.number.astype(int)));labels=dict(zip(key.model,key.label))
    numbered=style=='numbers'
    with plt.style.context('seaborn-v0_8-whitegrid'),plt.rc_context({'font.size':10,'axes.labelcolor':'#2f2149','text.color':'#2f2149','xtick.color':'#2f2149','ytick.color':'#2f2149','grid.alpha':.35,'grid.color':'#ddd6ef'}):
        fig=plt.figure(figsize=(13.5,8.7 if numbered else 5.8),dpi=160)
        gs=fig.add_gridspec(2 if numbered else 1,2,height_ratios=[3.8,2.] if numbered else [1],left=.07,right=.98,top=.88 if numbered else .82,bottom=.04 if numbered else .12,hspace=.38,wspace=.22)
        panels=[]
        for col,game in enumerate(['Connect4','Chess UCI']):
            ax=fig.add_subplot(gs[0,col]);all_points=points[points.game==game]
            d=all_points[all_points.finite] if method=='bt' else all_points
            panels.append((ax,d))
            ax.scatter(d.Automaton,d['Live Play'],s=33,color='#6c4ca8',edgecolors='#2f2149',linewidth=.5,zorder=3)
            lo=min(d.Automaton.min(),d['Live Play'].min());hi=max(d.Automaton.max(),d['Live Play'].max())
            ax.plot([lo,hi],[lo,hi],color='#9f89cf',linestyle=(0,(6,2,1.4,2)),linewidth=1.2)
            omitted=len(all_points)-len(d)
            ax.margins(.15);ax.set(title=game+(f' ({omitted} unbounded fits omitted)' if omitted else ''),xlabel='Automaton Elo',ylabel='Live-play Elo')
            ax.spines[['top','right']].set_visible(False)
        fig.canvas.draw()
        for ax,d in panels:
            xy=ax.transData.transform(d[['Automaton','Live Play']].to_numpy())
            obstacles=[Bbox.from_bounds(x-5,y-5,10,10) for x,y in xy];used=[];seen=set()
            for (name,row),(x,y) in zip(d.iterrows(),xy):
                if not numbered and (name not in SELECTED or name in seen):continue
                seen.add(name)
                text=str(numbers[name]) if numbered else labels[name];font=8 if numbered else 9
                tmp=ax.text(0,0,text,fontsize=font);box=tmp.get_window_extent(fig.canvas.get_renderer());w=box.width+7;h=box.height+5;tmp.remove()
                candidates=[]
                for radius in ([14,24,36,50,66,85,110] if numbered else [26,40,60,85,110,145,185]):
                    for deg in [90,45,135,-90,-45,-135,0,180]:
                        dx=radius*math.cos(math.radians(deg));dy=radius*math.sin(math.radians(deg))
                        b=Bbox.from_bounds(x+dx-w/2,y+dy-h/2,w,h)
                        if ax.bbox.contains(b.x0,b.y0) and ax.bbox.contains(b.x1,b.y1):
                            overlap=sum(b.overlaps(o) for o in obstacles+used);candidates.append((overlap,radius,dx,dy,b))
                if not candidates:continue
                _,radius,dx,dy,b=min(candidates,key=lambda t:(t[0],t[1]));used.append(b)
                ax.annotate(text,(row.Automaton,row['Live Play']),xytext=(dx*72/fig.dpi,dy*72/fig.dpi),textcoords='offset points',ha='center',va='center',fontsize=font,color='#2f2149',zorder=5,bbox=None if numbered else dict(facecolor='white',edgecolor='none',alpha=.85,pad=1.3),arrowprops=dict(arrowstyle='-',color='#b19dd8',lw=.65,shrinkA=2,shrinkB=5) if radius>18 else None)
        if numbered:
            legend=fig.add_subplot(gs[1,:]);legend.axis('off');legend.text(0,1.03,'MODEL KEY',weight='bold',fontsize=10,transform=legend.transAxes)
            rows=math.ceil(len(names)/3)
            for i,name in enumerate(names):legend.text((i//rows)/3,.9-(i%rows)*.105,f'{numbers[name]:2d}   {labels[name]}',fontsize=9.3,transform=legend.transAxes)
            legend.text(0,-.035,'Same model numbers across all variants. Two Gemini Connect4 points distinguish legal-move visibility.',fontsize=8.2,color='#756b84',transform=legend.transAxes)
        desc='Completed games only' if variant=='clean' else 'Completed games + illegal-move and bot-code forfeits'
        fig.suptitle(f'{method.upper() if method=="bt" else "Iterative Elo"} · {variant} · {style}',fontsize=16,weight='bold',y=.985)
        fig.text(.5,.94,desc+' · Legacy + current results',ha='center',fontsize=10,color='#756b84')
        for ext in ['png','pdf']:fig.savefig(dest/f'{style}.{ext}',dpi=200,bbox_inches='tight')
        plt.close(fig)


def render_paper(points, dest):
    """Export compact standalone iterative/all panels for side-by-side paper use."""
    from pathlib import Path
    labels = {
        'deepseek_v3.2': 'DeepSeek V3.2',
        'gemini_3_flash_preview': 'Gemini 3 Flash',
        'gpt_4o_mini': 'GPT-4o Mini',
        'gpt_5_mini': 'GPT-5 Mini',
        'qwen3_235b_a22b_2507': 'Qwen3 235B',
        'ministral_14b_2512': 'Ministral 14B',
    }
    dest = Path(dest)
    with plt.style.context('seaborn-v0_8-whitegrid'), plt.rc_context({
        'font.size': 8, 'axes.titlesize': 10, 'axes.labelsize': 9,
        'axes.labelcolor': '#2f2149', 'text.color': '#2f2149',
        'xtick.color': '#2f2149', 'ytick.color': '#2f2149',
        'grid.alpha': .35, 'grid.color': '#ddd6ef',
    }):
        for game, filename in [('Connect4', 'Connect4'), ('Chess UCI', 'Chess_UCI')]:
            fig, ax = plt.subplots(figsize=(4, 3.3), dpi=200)
            fig.subplots_adjust(left=.17, right=.97, bottom=.16, top=.89)
            d = points[points.game == game]
            ax.scatter(d.Automaton, d['Live Play'], s=19, color='#6c4ca8',
                       edgecolors='#2f2149', linewidth=.45, zorder=3)
            lo = min(d.Automaton.min(), d['Live Play'].min())
            hi = max(d.Automaton.max(), d['Live Play'].max())
            ax.plot([lo, hi], [lo, hi], color='#9f89cf',
                    linestyle=(0, (6, 2, 1.4, 2)), linewidth=.9)
            ax.margins(.15)
            ax.set(title='Connect 4' if game == 'Connect4' else 'Chess',
                   xlabel='Automaton Elo', ylabel='Live-play Elo')
            ax.spines[['top', 'right']].set_visible(False)
            from matplotlib.ticker import MaxNLocator
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
            fig.canvas.draw()
            xy = ax.transData.transform(d[['Automaton', 'Live Play']].to_numpy())
            obstacles = [Bbox.from_bounds(x-6, y-6, 12, 12) for x, y in xy]
            used, seen = [], set()
            for (name, row), (x, y) in zip(d.iterrows(), xy):
                if name not in labels or name in seen:
                    continue
                seen.add(name)
                text = labels[name]
                tmp = ax.text(0, 0, text, fontsize=7.5)
                box = tmp.get_window_extent(fig.canvas.get_renderer())
                w, h = box.width+6, box.height+5
                tmp.remove()
                candidates = []
                for radius in [24, 36, 50, 70, 95, 125, 160]:
                    for deg in [90, -90, 45, 135, -45, -135, 0, 180]:
                        dx = radius*math.cos(math.radians(deg))
                        dy = radius*math.sin(math.radians(deg))
                        b = Bbox.from_bounds(x+dx-w/2, y+dy-h/2, w, h)
                        if ax.bbox.contains(b.x0, b.y0) and ax.bbox.contains(b.x1, b.y1):
                            candidates.append((sum(b.overlaps(o) for o in obstacles+used), radius, dx, dy, b))
                if not candidates:
                    raise ValueError(f'No label position for {name}')
                _, radius, dx, dy, b = min(candidates, key=lambda t: (t[0], t[1]))
                used.append(b)
                ax.annotate(text, (row.Automaton, row['Live Play']),
                            xytext=(dx*72/fig.dpi, dy*72/fig.dpi),
                            textcoords='offset points', ha='center', va='center',
                            fontsize=7.5, zorder=5,
                            bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=.6),
                            arrowprops=dict(arrowstyle='-', color='#b19dd8', lw=.55,
                                            shrinkA=2, shrinkB=4))
            fig.savefig(dest/f'live_play_{filename}.pdf')
            fig.savefig(f'/tmp/live_play_{filename}_paper.png', dpi=200)
            plt.close(fig)
