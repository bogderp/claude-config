import json,os,glob,time,collections as C,datetime as dt
root=os.path.expanduser('~/.claude/projects'); cutoff=time.time()-30*86400
def t(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
tot=0; bust=C.Counter(); bustn=C.Counter(); tail=0; gaps=C.Counter(); dup=0; seen_ids=C.Counter()
for p in glob.glob(root+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(p)<cutoff: continue
    prev=None; prevctx=0; ids=set()
    for line in open(p,errors='ignore'):
        try:d=json.loads(line)
        except:continue
        m=d.get('message') or {}
        if d.get('type')!='assistant' or not m.get('usage'): continue
        mid=m.get('id')
        if mid in ids: continue   # same API response split into multiple lines
        ids.add(mid)
        u=m['usage']; cr,cw=u.get('cache_read_input_tokens',0),u.get('cache_creation_input_tokens',0); ctx=cr+cw+u.get('input_tokens',0)
        tot+=cw; ts=t(d['timestamp']) if d.get('timestamp') else None
        if prev is None: kind='first-call'
        elif cw>20000 and cr<0.7*prevctx:
            g=ts-prev if ts and prev else 0
            kind='bust:idle>1h' if g>3600 else 'bust:idle5m-1h' if g>300 else 'bust:no-idle'
            gaps[int(g//60)]+=1
        else: kind='normal-tail'
        bust[kind]+=cw; bustn[kind]+=1
        prev=ts; prevctx=ctx
print("cache-write tokens by cause (deduped by message id):")
for k,v in bust.most_common(): print(f"  {k:16} {v/tot:5.0%}  calls={bustn[k]}")
print("bust gap minutes (top):",sorted(gaps.items(),key=lambda x:-x[1])[:10])
