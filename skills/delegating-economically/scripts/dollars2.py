import json,os,glob,time,collections as C
root=os.path.expanduser('~/.claude/projects'); cutoff=time.time()-30*86400
P={'fable':(10,50,.25),'opus':(4,20,.20),'sonnet':(2,10,.20),'haiku':(.1,.5,.01)}  # in,out,cache_read ; cache write (1h) = 2x in
def fam(m):
    for f in P:
        if f in (m or ''): return f
def cost(f,i,cr,cw,o): a,b,c=P[f]; return (i*a+cw*2*a+cr*c+o*b)/1e6
by=C.Counter(); comp=C.Counter(); sub_sonnet=0; sub_now=0; rot_save=0; days=set(); main_now=0
for p in glob.glob(root+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(p)<cutoff: continue
    sub='/subagents/' in p; ids=set()
    for line in open(p,errors='ignore'):
        try:d=json.loads(line)
        except:continue
        m=d.get('message') or {}
        if d.get('type')!='assistant' or not m.get('usage'): continue
        if m.get('id') in ids: continue
        ids.add(m.get('id')); f=fam(m.get('model'))
        if not f: continue
        u=m['usage'];i,cr,cw,o=u.get('input_tokens',0),u.get('cache_read_input_tokens',0),u.get('cache_creation_input_tokens',0),u.get('output_tokens',0)
        c=cost(f,i,cr,cw,o); by[('sub' if sub else 'main',f)]+=c; days.add((d.get('timestamp') or '')[:10])
        a,b,cc=P[f]; comp['cache_read']+=cr*cc/1e6; comp['cache_write']+=cw*2*a/1e6; comp['output']+=o*b/1e6; comp['input']+=i*a/1e6
        if sub and f=='opus': sub_now+=c; sub_sonnet+=cost('sonnet',i,cr,cw,o)
        ctx=i+cr+cw
        if not sub and ctx>200000 and False: rot_save+=(ctx-120000)*cc/1e6   # rotate at 200k -> fresh session averages ~120k
T=sum(by.values())
print(f"30-day est total ${T:,.0f} over {len(days)} active days (${T/len(days):,.0f}/day)")
for k,v in by.most_common(): print(f"  {k}: ${v:,.0f} ({v/T:.0%})")
print("components:",{k:f"${v:,.0f} ({v/T:.0%})" for k,v in comp.items()})
print(f"opus subagents -> sonnet: ${sub_now:,.0f} -> ${sub_sonnet:,.0f} (save ${sub_now-sub_sonnet:,.0f})")
print(f"rotate main sessions at 200k (cache-read only, rough): save ~${rot_save:,.0f}")

# idle-resume busts on big main sessions
