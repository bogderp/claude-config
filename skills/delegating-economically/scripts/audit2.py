import json,os,glob,time,collections as C
root=os.path.expanduser('~/.claude/projects'); cutoff=time.time()-30*86400
comp=C.Counter(); bucket=C.Counter(); bcalls=C.Counter(); submodel=C.Counter(); mainmodel=C.Counter(); bigreads=C.Counter(); exact=C.Counter()
def fam(m):
    for f in('opus','sonnet','haiku','fable'):
        if f in (m or ''): return f
    return m
for p in glob.glob(root+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(p)<cutoff: continue
    sub='/subagents/' in p; ids={}
    for line in open(p,errors='ignore'):
        try:d=json.loads(line)
        except:continue
        m=d.get('message') or {}
        if d.get('type')=='assistant' and m.get('usage') and m.get('model')!='<synthetic>':
            u=m['usage'];i,cr,cw,o=u.get('input_tokens',0),u.get('cache_read_input_tokens',0),u.get('cache_creation_input_tokens',0),u.get('output_tokens',0)
            un=i+cr*.1+cw*1.25+o*5; comp['input']+=i;comp['cache_read']+=cr*.1;comp['cache_write']+=cw*1.25;comp['output']+=o*5
            ctx=i+cr+cw; b='<100k' if ctx<1e5 else '100-200k' if ctx<2e5 else '200-400k' if ctx<4e5 else '400k+'
            bucket[b]+=un; bcalls[b]+=1; exact[m.get('model')]+=un
            (submodel if sub else mainmodel)[fam(m.get('model'))]+=un
            for c in m.get('content') or []:
                if isinstance(c,dict) and c.get('type')=='tool_use' and c['name']=='Read': ids[c['id']]=c['input'].get('file_path')
        elif d.get('type')=='user' and isinstance(m.get('content'),list):
            for x in m['content']:
                if isinstance(x,dict) and x.get('tool_use_id') in ids:
                    L=len(json.dumps(x.get('content')))
                    if L>40000: bigreads[ids[x['tool_use_id']]]+=L
T=sum(comp.values())
print("cost components:",{k:f"{v/T:.0%}" for k,v in comp.items()})
print("by ctx bucket (share of spend, calls):",{k:(f"{bucket[k]/T:.0%}",bcalls[k]) for k in['<100k','100-200k','200-400k','400k+']})
print("main by model:",{k:f"{v/T:.0%}" for k,v in mainmodel.most_common()}); print("subagent by model:",{k:f"{v/T:.0%}" for k,v in submodel.most_common()})
print("exact models:",{k:f"{v/T:.0%}" for k,v in exact.most_common(8)})
print("big reads:");[print(f"  {v//1000}k chars  {k}") for k,v in bigreads.most_common(10)]
