import json,os,sys,glob,time,collections as C
root=os.path.expanduser('~/.claude/projects'); cutoff=time.time()-30*86400
W={'in':1,'cr':0.1,'cw':1.25,'out':5}  # relative weights vs base input price
def fam(m): 
    m=(m or '').lower()
    for f in('opus','sonnet','haiku','fable'):
        if f in m: return f
    return m or '?'
sess=[];tool_out=C.Counter();tool_n=C.Counter();model_tot=C.Counter();sub_model=C.Counter();sub_type=C.Counter()
skill=C.Counter();big=[];compacts=0;bash_cmds=C.Counter()
for p in glob.glob(root+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(p)<cutoff: continue
    is_sub='/subagents/' in p
    s=dict(path=p.replace(root,''),sub=is_sub,units=0,turns=0,peak=0,model=C.Counter(),compact=0,user=0,start=None,end=None)
    pending={}
    for line in open(p,errors='ignore'):
        try:d=json.loads(line)
        except:continue
        ts=d.get('timestamp'); 
        if ts: s['start']=s['start'] or ts; s['end']=ts
        if d.get('isCompactSummary') or (d.get('type')=='system' and d.get('subtype')=='compact_boundary'): s['compact']+=1
        m=d.get('message') or {}
        if d.get('type')=='assistant':
            u=m.get('usage') or {}
            i,cr,cw,o=u.get('input_tokens',0),u.get('cache_read_input_tokens',0),u.get('cache_creation_input_tokens',0),u.get('output_tokens',0)
            un=i*W['in']+cr*W['cr']+cw*W['cw']+o*W['out']
            f=fam(m.get('model'))
            if f=='<synthetic>':continue
            s['units']+=un; s['turns']+=1; s['model'][f]+=un; model_tot[f]+=un
            s['peak']=max(s['peak'],i+cr+cw)
            for c in m.get('content') or []:
                if isinstance(c,dict) and c.get('type')=='tool_use':
                    n=c['name']; inp=c.get('input',{}); pending[c['id']]=n
                    if n in('Agent','Task'):
                        sub_model[inp.get('model') or 'inherit']+=1; sub_type[inp.get('subagent_type') or 'general']+=1
                    if n=='Skill': skill[inp.get('skill')]+=1
                    if n=='Bash': bash_cmds[(inp.get('command') or '').split()[0] if inp.get('command') else '']+=1
        elif d.get('type')=='user':
            c=m.get('content')
            if isinstance(c,str): s['user']+=1
            elif isinstance(c,list):
                for x in c:
                    if isinstance(x,dict) and x.get('type')=='tool_result':
                        n=pending.get(x.get('tool_use_id'),'?'); cc=x.get('content'); L=len(json.dumps(cc)) if not isinstance(cc,str) else len(cc)
                        tool_out[n]+=L; tool_n[n]+=1
                        if L>40000: big.append((L,n,s['path'][:70]))
                    elif isinstance(x,dict) and x.get('type')=='text': s['user']+=1
    if s['turns']: sess.append(s)
tot=sum(s['units'] for s in sess)
print(f"sessions {sum(not s['sub'] for s in sess)} main, {sum(s['sub'] for s in sess)} subagent; total units {tot/1e6:.1f}M (base-input-token equivalents)")
print("by model:",{k:f"{v/tot:.0%}" for k,v in model_tot.most_common()})
print("main vs sub:",f"{sum(s['units'] for s in sess if not s['sub'])/tot:.0%} main")
print("compacted sessions:",sum(1 for s in sess if s['compact']), " total compactions",sum(s['compact'] for s in sess))
pk=sorted(s['peak'] for s in sess if not s['sub']); print("peak ctx main p50/p90/max:",pk[len(pk)//2],pk[int(len(pk)*.9)],pk[-1])
print("sessions with peak>150k:",sum(1 for s in sess if s['peak']>150000), " >300k:",sum(1 for s in sess if s['peak']>300000))
# cost concentration by turn depth: units from turns at context>100k
def mix(s): return {k:round(v/s['units']*100) for k,v in s['model'].items()}
print("\nTop 12 sessions:")
for s in sorted(sess,key=lambda s:-s['units'])[:12]:
    print(f"  {s['units']/1e6:6.2f}M {s['turns']:4}t peak{s['peak']//1000:4}k cmp{s['compact']} usr{s['user']:3} {mix(s)} {s['path'][:75]}")
print("\ntop 10 share:",f"{sum(s['units'] for s in sorted(sess,key=lambda s:-s['units'])[:10])/tot:.0%}")
print("\nTool output chars (total, count, avg):")
for n,v in tool_out.most_common(14): print(f"  {n:45} {v/1e6:6.1f}M {tool_n[n]:6} {v//tool_n[n]:7}")
print("\nAgent model param:",dict(sub_model)); print("subagent types:",sub_type.most_common(12))
print("skills:",skill.most_common(15)); print("bash heads:",bash_cmds.most_common(12))
print("huge results (>40k chars):",len(big)); [print("  ",b) for b in sorted(big,reverse=True)[:8]]
