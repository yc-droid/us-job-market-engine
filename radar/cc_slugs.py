# Enumerate ATS company board slugs from Common Crawl CDX (free). Output: ats_slugs.json {ats: [slug,...]}
import json, urllib.request, urllib.parse, re, concurrent.futures as cf, time
CRAWLS=["CC-MAIN-2026-39","CC-MAIN-2026-34","CC-MAIN-2026-30","CC-MAIN-2026-25"]
HOSTS={"greenhouse":["boards.greenhouse.io","job-boards.greenhouse.io"],"lever":["jobs.lever.co"],"ashby":["jobs.ashbyhq.com"],"workable":["apply.workable.com"],"smartrecruiters":["jobs.smartrecruiters.com"]}
BAD={"embed","api","v1","jobs","job","static","assets","favicon.ico","robots.txt","sitemap.xml","careers","search","",":","404","widget"}
def get(u):
    for a in range(5):
        try: return urllib.request.urlopen(u,timeout=120).read().decode()
        except Exception: time.sleep(5*(a+1))
    return ""
def pages(c,h):
    s=get(f"https://index.commoncrawl.org/{c}-index?url={h}/*&output=json&showNumPages=true")
    try: return json.loads(s)["pages"]
    except Exception: return 0
tasks=[]
for c in CRAWLS:
    for ats,hs in HOSTS.items():
        for h in hs:
            for p in range(pages(c,h)): tasks.append((c,ats,h,p))
print("cdx pages",len(tasks),flush=True)
def run(t):
    c,ats,h,p=t; s=get(f"https://index.commoncrawl.org/{c}-index?url={h}/*&output=json&fl=url&page={p}")
    out=set()
    for line in s.splitlines():
        try: u=json.loads(line)["url"]
        except Exception: continue
        path=urllib.parse.urlparse(u).path.strip("/").split("/")
        slug=path[0].lower() if path else ""
        if ats=="greenhouse" and slug=="embed":
            q=urllib.parse.parse_qs(urllib.parse.urlparse(u).query); slug=(q.get("for") or [""])[0].lower()
        if slug and slug not in BAD and re.fullmatch(r"[a-z0-9][a-z0-9\-_.]{0,80}",slug): out.add(slug)
    return ats,out
res={k:set() for k in HOSTS}
with cf.ThreadPoolExecutor(4) as ex:
    for i,(ats,s) in enumerate(ex.map(run,tasks)):
        res[ats]|=s
        if i%10==0: print(i,{k:len(v) for k,v in res.items()},flush=True)
json.dump({k:sorted(v) for k,v in res.items()},open("ats_slugs.json","w"))
print("DONE",{k:len(v) for k,v in res.items()})
