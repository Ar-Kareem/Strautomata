import json, re, glob, os, sys, csv
from html.parser import HTMLParser

def cells_of(table_html):
    """Return list of rows; each row = (attrs_of_tr, [(td_class, text, td_attrs), ...])"""
    rows=[]
    class P(HTMLParser):
        def __init__(s):
            super().__init__(); s.in_body=False; s.row=None; s.cell=None; s.hdr=[]; s.in_th=False; s.th=''
        def handle_starttag(s,tag,attrs):
            a=dict(attrs)
            if tag=='tbody': s.in_body=True
            if tag=='th': s.in_th=True; s.th=''; s.th_attrs=a
            if tag=='tr' and s.in_body: s.row=(a,[])
            if tag=='td' and s.row is not None: s.cell=[a,'']
            if tag=='a' and s.cell is not None and 'href' in a: s.cell[0]['href']=a['href']
        def handle_endtag(s,tag):
            if tag=='th': s.in_th=False; s.hdr.append(s.th.strip())
            if tag=='td' and s.cell is not None:
                s.row[1].append((s.cell[0], re.sub(r'\s+',' ',s.cell[1]).strip())); s.cell=None
            if tag=='tr' and s.row is not None: rows.append(s.row); s.row=None
        def handle_data(s,d):
            if s.in_th: s.th+=d
            if s.cell is not None: s.cell[1]+=d
    p=P(); p.feed(table_html); return p.hdr, rows

def parse(path):
    d=json.load(open(path))
    hdr,rows=cells_of(d['table'])
    # n problems from problem_table header
    phdr,prows=cells_of(d['problem_table'])
    nprob=len([h for h in phdr if re.match(r'^(\d+|[A-Za-z]?\d+[a-z]?|P\d+|Problem \d+)$',h)])
    out=[]
    ci={h:i for i,h in enumerate(hdr)}
    acc_i=[i for i,h in enumerate(hdr) if h.startswith('Accuracy') or h.startswith('Score')][0]
    cost_i=ci.get('Cost')
    for tra,cells in rows:
        if 'model-row' not in tra.get('class',''): continue
        name=cells[1][1].replace('⚠️','').strip()
        href=cells[1][0].get('href','')
        acc=cells[acc_i][1]
        m=re.match(r'([\d.]+)%',acc); accv=float(m.group(1)) if m else ''
        cost=cells[cost_i][1] if cost_i is not None else ''
        m=re.match(r'\$([\d.,]+)',cost); costv=float(m.group(1).replace(',','')) if m else ''
        out.append(dict(config=tra.get('data-config'),name=name,href=href,acc_raw=acc,acc=accv,cost_raw=cost,cost=costv,predicted=cells[acc_i][0].get('data-predicted')))
    return hdr,phdr,nprob,out

if __name__=='__main__':
    for f in sorted(glob.glob('raw/matharena_*.resp')):
        cid=os.path.basename(f)[len('matharena_'):-5]
        try: hdr,phdr,nprob,rows=parse(f)
        except Exception as e: print(cid,'ERR',e); continue
        astra=[r for r in rows if 'astra' in r['name'].lower()]
        fable=[r for r in rows if 'fable-5.1' in r['name'].lower() or 'fable 5.1' in r['name'].lower()]
        print(f"{cid:35s} rows={len(rows):3d} nprob={nprob:4d} cost_col={'Cost' in hdr} acc_hdr={[h for h in hdr if 'Acc' in h or 'Score' in h]}")
        for r in astra+fable: print('    ',r['name'],r['acc_raw'],r['cost_raw'],r['predicted'])
