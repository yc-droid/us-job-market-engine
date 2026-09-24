# Blitz count-only market map for every role in taxonomy.TAX. ~1 record per call.
import json, urllib.request, concurrent.futures as cf, time
from taxonomy import TAX
import os; K=os.environ.get("BLITZ_API_KEY") or exit("Set BLITZ_API_KEY (https://blitz-api.ai) to use the Blitz market map")
def cnt(job,company=None):
    body={"job":job,"max_results":1}
    if company: body["company"]=company
    for a in range(6):
        try:
            req=urllib.request.Request("https://api.blitz-api.ai/v2/jobs/search",json.dumps(body).encode(),{"Content-Type":"application/json","x-api-key":K})
            return json.load(urllib.request.urlopen(req,timeout=90))["total_results"]
        except Exception: time.sleep(2+a*3)
US={"country_code":{"include":["US"]}}
HQUS={"hq":{"country_code":{"include":["US"]}}}
tasks=[]
for fam,role,inc,exc,b in TAX:
    t={"title":{"include":inc,**({"exclude":exc} if exc else {})}}
    for d in range(30,271,30): tasks.append((role,f"d{d}",{**t,"location":US,"date_posted":{"last_days":d}},None))
    q={**t,"location":US,"date_posted":{"last_days":90}}
    tasks.append((role,"remote",{**q,"work_arrangement":{"include":["Remote Solely","Remote OK"]}},None))
    tasks.append((role,"contract",{**q,"employment_type":{"include":["CONTRACTOR","TEMPORARY"]}},None))
    for s in ["0-2","2-5","5-10","10+"]: tasks.append((role,f"sen_{s}",{**q,"seniority":{"include":[s]}},None))
    tasks.append((role,"uscos_us",q,HQUS))
    for cc in ["IN","PH"]: tasks.append((role,f"uscos_{cc}",{**t,"location":{"country_code":{"include":[cc]}},"date_posted":{"last_days":90}},HQUS))
    tasks.append((role,"all_IN",{**t,"location":{"country_code":{"include":["IN"]}},"date_posted":{"last_days":90}},None))
for d in range(30,271,30): tasks.append(("__base",f"d{d}",{"location":US,"date_posted":{"last_days":d}},None))
with cf.ThreadPoolExecutor(16) as ex: res=list(ex.map(lambda t:(t[0],t[1],cnt(t[2],t[3])),tasks))
out={}
for r,k,v in res: out.setdefault(r,{})[k]=v
meta={role:{"family":fam,"bound":b} for fam,role,inc,exc,b in TAX}
json.dump({"meta":meta,"counts":out},open("market_map.json","w"),indent=1)
print("calls",len(tasks),"nulls",sum(1 for x in res if x[2] is None))
