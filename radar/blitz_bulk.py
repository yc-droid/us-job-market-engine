# Bulk-pull US postings (last 90d) for offshorable roles from Blitz into blitz.db. Splits cells to beat the 5k/query cap.
import json, sqlite3, time, threading, urllib.request, concurrent.futures as cf
from taxonomy import TAX
import os; K=os.environ.get("BLITZ_API_KEY") or exit("Set BLITZ_API_KEY (https://blitz-api.ai) to use the Blitz market map"); MIN_SCORE=40
DB=sqlite3.connect("blitz.db",check_same_thread=False,timeout=60); DB.execute("PRAGMA journal_mode=WAL"); L=threading.Lock()
DB.executescript("""CREATE TABLE IF NOT EXISTS jobs(url TEXT PRIMARY KEY, role TEXT, family TEXT, title TEXT, company TEXT, company_li TEXT, city TEXT, posted TEXT,
 seniority TEXT, arrangement TEXT, contract INT DEFAULT 0, summary TEXT);
CREATE TABLE IF NOT EXISTS cells(key TEXT PRIMARY KEY, total INT, pulled INT, truncated INT);""")
CITIES=json.load(open("top_cities.json"))
R={r["role"]:r for r in json.load(open("role_scores.json"))}
ROLES=[(f,role,inc,exc) for f,role,inc,exc,b in TAX if role in R and R[role]["score"]>=MIN_SCORE and b<2]
done={k for (k,) in DB.execute("SELECT key FROM cells")}
def post(job,cursor=None,n=50):
    b={"job":{**job,"date_posted":{"last_days":90}},"max_results":n}
    if cursor: b["cursor"]=cursor
    for a in range(6):
        try:
            req=urllib.request.Request("https://api.blitz-api.ai/v2/jobs/search",json.dumps(b).encode(),{"Content-Type":"application/json","x-api-key":K})
            return json.load(urllib.request.urlopen(req,timeout=90))
        except Exception: time.sleep(2+a*3)
    return {"results":[],"total_results":0}
def pull(key,job,tag,fam,role):
    if key in done: return 0
    rows=[];cur=None;total=None
    while True:
        d=post(job,cur); total=total if total is not None else d.get("total_results",0)
        rows+=d.get("results",[]); cur=d.get("cursor")
        if not cur or not d.get("results"): break
    with L:
        for r in rows:
            DB.execute("""INSERT INTO jobs(url,role,family,title,company,company_li,city,posted,seniority,arrangement,contract,summary) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
             ON CONFLICT(url) DO UPDATE SET contract=MAX(contract,excluded.contract), seniority=COALESCE(jobs.seniority,excluded.seniority), arrangement=COALESCE(jobs.arrangement,excluded.arrangement)""",
             (r["url"],role,fam,r["title"],r["company_name"],r["company_linkedin_url"],(r.get("location") or {}).get("city"),(r.get("date_posted") or "")[:10],tag.get("sen"),tag.get("arr"),tag.get("contract",0),r.get("ai_summary")))
        DB.execute("INSERT OR REPLACE INTO cells VALUES(?,?,?,?)",(key,total,len(rows),int(total>len(rows)))); DB.commit()
    return len(rows)
def count(job): return post(job,n=1).get("total_results",0)
def plan(fam,role,inc,exc):
    t={"title":{"include":inc,**({"exclude":exc} if exc else {})}}; US={"country_code":{"include":["US"]}}
    out=[]
    for s in ["0-2","2-5","5-10","10+"]:
        for a in ["On-site","Hybrid","Remote OK","Remote Solely"]:
            j={**t,"location":US,"seniority":{"include":[s]},"work_arrangement":{"include":[a]}}; tag={"sen":s,"arr":a}; k=f"{role}|{s}|{a}"
            if k+"|all" in done or all(k+f"|{c}" in done for c in CITIES+["rest"]): continue
            n=count(j)
            if n<=5000: out.append((k+"|all",j,tag))
            else:
                for c in CITIES: out.append((k+f"|{c}",{**j,"location":{**US,"city":{"include":[c]}}},tag))
                out.append((k+"|rest",{**j,"location":{**US,"city":{"exclude":CITIES}}},tag))
    j={**t,"location":US,"employment_type":{"include":["CONTRACTOR","TEMPORARY"]}}
    for s in ["0-2","2-5","5-10","10+"]: out.append((f"{role}|contract|{s}",{**j,"seniority":{"include":[s]}},{"contract":1}))
    return [(k,j,tag,fam,role) for k,j,tag in out]
with cf.ThreadPoolExecutor(8) as ex: cells=[c for p in ex.map(lambda r:plan(*r),ROLES) for c in p]
print("roles",len(ROLES),"cells",len(cells),flush=True); n=[0,0]
with cf.ThreadPoolExecutor(20) as ex:
    for k in ex.map(lambda c:pull(*c),cells):
        n[0]+=1;n[1]+=k
        if n[0]%100==0: print(f"cells {n[0]}/{len(cells)} rows {n[1]}",flush=True)
print("DONE",DB.execute("select count(*),sum(truncated) from jobs, (select sum(truncated) truncated from cells)").fetchone())
