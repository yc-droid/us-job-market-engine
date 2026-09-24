import json,math
M=json.load(open("market_map.json")); C=M["counts"]; meta=M["meta"]
def monthly(r): c=[r[f"d{x}"] for x in range(30,271,30)]; return [c[0]]+[c[i]-c[i-1] for i in range(1,9)]
bm=monthly(C["__base"])
rows=[]
for role,r in C.items():
    if role=="__base": continue
    m=monthly(r); p=[m[i]/bm[i]*1e6 for i in range(9)]
    trend=(sum(p[1:4])/sum(p[5:8])-1)*100 if sum(p[5:8]) else 0
    d90=r["d90"] or 1; us=r["uscos_us"] or 1
    ind=r["uscos_IN"]/us; ph=r["uscos_PH"]/us
    rem=r["remote"]/d90*100; con=r["contract"]/d90*100
    b=meta[role]["bound"]
    s=min(ind/0.5,1)*35+min(rem/40,1)*20+min(con/25,1)*15+{0:20,1:8,2:0}[b]+max(0,min((trend+20)/80,1))*10
    sen=sum(r[f"sen_{x}"] for x in ["0-2","2-5","5-10","10+"]) or 1
    rows.append({"family":meta[role]["family"],"role":role,"bound":b,"us_90d":r["d90"],"trend":round(trend),"remote":round(rem,1),"contract":round(con,1),
      "uscos_us":r["uscos_us"],"uscos_in":r["uscos_IN"],"uscos_ph":r["uscos_PH"],"india_ratio":round(ind,3),"ph_ratio":round(ph,3),"all_in":r["all_IN"],
      "junior":round(r["sen_0-2"]/sen*100),"senior":round((r["sen_5-10"]+r["sen_10+"])/sen*100),"score":round(s),"opportunity":round(s*math.log10(max(r["d90"],10)),1)})
rows.sort(key=lambda x:-x["opportunity"])
json.dump(rows,open("role_scores.json","w"),indent=1)
print(f"{'role':30}{'fam':16}{'US 90d':>8}{'trend':>6}{'rem%':>6}{'con%':>6}{'IN/US':>7}{'PH/US':>7}{'score':>6}{'opp':>6}")
for x in rows: print(f"{x['role'][:30]:30}{x['family'][:15]:16}{x['us_90d']:>8,}{x['trend']:>6}{x['remote']:>6.0f}{x['contract']:>6.0f}{x['india_ratio']:>7.2f}{x['ph_ratio']:>7.2f}{x['score']:>6}{x['opportunity']:>6}")
