import sqlite3,statistics as st,json,csv,collections
from taxonomy import TAX
DB=sqlite3.connect("jobs.db")
fam={r:f for f,r,*_ in TAX}
def annual(lo,hi,per): m=(lo+hi)/2; return m*2080 if per=="hour" else m
# companies with India presence
india_cos={s for (s,) in DB.execute("SELECT DISTINCT ats||':'||slug FROM jobs WHERE country='IN'")}
roles={}
for ats,slug,company,role,sal_min,sal_max,per,rem in DB.execute("SELECT ats,slug,company,role,sal_min,sal_max,sal_period,remote FROM jobs WHERE country='US'"):
    r=roles.setdefault(role,{"n":0,"cos":set(),"sal":[],"remote":0,"india_co_jobs":0})
    r["n"]+=1; r["cos"].add(ats+":"+slug); r["remote"]+=rem or 0
    if sal_min: r["sal"].append(annual(sal_min,sal_max,per))
    if ats+":"+slug in india_cos: r["india_co_jobs"]+=1
inr={}
for role,c in DB.execute("SELECT role,count(*) FROM jobs WHERE country='IN' GROUP BY 1"): inr[role]=c
out=[]
for role,r in roles.items():
    s=sorted(r["sal"])
    out.append({"role":role,"family":fam.get(role,"Other"),"us_jobs":r["n"],"companies":len(r["cos"]),"remote_pct":round(r["remote"]/r["n"]*100),
      "sal_n":len(s),"sal_p25":round(s[len(s)//4]) if len(s)>=8 else None,"sal_med":round(st.median(s)) if len(s)>=5 else None,"sal_p75":round(s[3*len(s)//4]) if len(s)>=8 else None,
      "in_jobs":inr.get(role,0),"in_to_us":round(inr.get(role,0)/r["n"],2),"pct_at_india_cos":round(r["india_co_jobs"]/r["n"]*100)})
out.sort(key=lambda x:-x["us_jobs"])
json.dump(out,open("ats_role_stats.json","w"),indent=1)
tot=DB.execute("SELECT count(*),sum(country='US'),sum(country='IN'),count(DISTINCT ats||slug),sum(country='US' and sal_min is not null) FROM jobs").fetchone()
print("jobs %s | US %s | IN %s | boards %s | US w/ salary %s"%tot)
print(f"{'role':30}{'US':>7}{'cos':>6}{'rem%':>6}{'sal_n':>6}{'median':>9}{'IN':>6}{'IN/US':>6}{'@INco%':>7}")
for x in out[:45]: print(f"{x['role'][:30]:30}{x['us_jobs']:>7}{x['companies']:>6}{x['remote_pct']:>6}{x['sal_n']:>6}{(x['sal_med'] or 0)/1000:>8.0f}K{x['in_jobs']:>6}{x['in_to_us']:>6}{x['pct_at_india_cos']:>7}")
