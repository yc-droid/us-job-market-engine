# Crawl public ATS boards (Greenhouse / Lever / Ashby / SmartRecruiters) -> SQLite jobs.db
# Full description stored (zlib) only for US + India jobs. Resumable: skips boards already crawled today.
import requests, random, json, re, sys, sqlite3, zlib, time, html, urllib.request, concurrent.futures as cf, threading, datetime
from taxonomy import TAX
DB=sqlite3.connect("jobs.db",check_same_thread=False,timeout=60); L=threading.Lock()
DB.execute("PRAGMA journal_mode=WAL"); DB.execute("PRAGMA synchronous=NORMAL")
DB.executescript("""
CREATE TABLE IF NOT EXISTS boards(ats TEXT, slug TEXT, company TEXT, n_jobs INT, n_us INT, n_in INT, status TEXT, crawled TEXT, PRIMARY KEY(ats,slug));
CREATE TABLE IF NOT EXISTS jobs(ats TEXT, slug TEXT, job_id TEXT, company TEXT, title TEXT, family TEXT, role TEXT, location TEXT, country TEXT,
  remote INT, employment_type TEXT, department TEXT, posted TEXT, sal_min REAL, sal_max REAL, sal_period TEXT, url TEXT, desc BLOB, seen TEXT,
  PRIMARY KEY(ats,slug,job_id));
""")
TODAY=datetime.date.today().isoformat()
ST="AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
STN="Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|San Francisco|Seattle|Boston|Chicago|Austin|Los Angeles|Atlanta|Denver|Miami"
RE_US=re.compile(r"United States|\bUSA?\b|U\.S\.|\bAmericas\b|, ("+"|".join(ST)+r")\b|\b("+STN+r")\b")
RE_IN=re.compile(r"India|Bengaluru|Bangalore|Hyderabad|Pune|Chennai|Mumbai|Gurgaon|Gurugram|Noida|New Delhi|Delhi|Kolkata|Ahmedabad|Kochi|Jaipur",re.I)
RE_REM=re.compile(r"remote|anywhere|distributed",re.I)
def country(loc):
    if not loc: return None
    if RE_IN.search(loc): return "IN"
    if RE_US.search(loc): return "US"
    return "OTHER"
CL=[(fam,role,[i.lower() for i in inc],[e.lower() for e in exc]) for fam,role,inc,exc,b in TAX]
def classify(t):
    tl=" "+(t or "").lower()+" "
    for fam,role,inc,exc in CL:
        if any(i in tl for i in inc) and not any(e in tl for e in exc): return fam,role
    return "Other","Other"
RE_SAL=re.compile(r"\$\s?([\d,]{2,}(?:\.\d+)?)\s*([kK])?\s*(?:USD)?\s*(?:/\s*(?:yr|year|hr|hour))?\s*(?:-|–|—|to)\s*\$?\s?([\d,]{2,}(?:\.\d+)?)\s*([kK])?\s*(?:USD)?\s*(per hour|/\s*hr|/\s*hour|an hour|hourly)?")
def salary(text):
    m=RE_SAL.search(text or "")
    if not m: return None,None,None
    lo=float(m.group(1).replace(",",""))*(1000 if m.group(2) else 1); hi=float(m.group(3).replace(",",""))*(1000 if m.group(4) else 1)
    per="hour" if (m.group(5) or hi<500) else "year"
    if hi<lo or (per=="year" and not 15000<=lo<=900000) or (per=="hour" and not 7<=lo<=500): return None,None,None
    return lo,hi,per
TL=threading.local()
def get(u,data=None):
    if not hasattr(TL,"s"): TL.s=requests.Session(); TL.s.headers["User-Agent"]="us-job-market-engine (+https://github.com/yc-droid/us-job-market-engine)"
    for a in range(3):
        try:
            r=TL.s.get(u,timeout=(5,15))
            if r.status_code in (404,410,403,400): return None
            if r.status_code==429: time.sleep(10*(a+1)); continue
            if r.ok: return r.json()
        except Exception: time.sleep(2*(a+1))
    return None
strip=lambda h: re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",html.unescape(h or ""))))
def norm_greenhouse(slug):
    d=get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    if not d or "jobs" not in d: return None
    for j in d["jobs"]:
        txt=strip(j.get("content"))
        yield dict(job_id=str(j["id"]),company=j.get("company_name") or slug,title=j.get("title"),location=(j.get("location") or {}).get("name"),
            employment_type=None,department=", ".join(x["name"] for x in j.get("departments") or []),posted=(j.get("first_published") or j.get("updated_at") or "")[:10],
            url=j.get("absolute_url"),text=txt)
def norm_lever(slug):
    d=get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if not isinstance(d,list): return None
    for j in d:
        c=j.get("categories") or {}; sr=j.get("salaryRange") or {}
        txt=" ".join(filter(None,[j.get("descriptionPlain"),*[strip(x.get("content")) for x in j.get("lists") or []],j.get("additionalPlain")]))
        if sr.get("min"): txt=f"${sr['min']} - ${sr['max']} {'per hour' if sr.get('interval')=='per-hour-wage' else ''} "+txt
        yield dict(job_id=j["id"],company=slug,title=j.get("text"),location=c.get("location"),employment_type=c.get("commitment"),department=c.get("team"),
            posted=datetime.datetime.fromtimestamp(j.get("createdAt",0)/1000,datetime.UTC).date().isoformat(),url=j.get("hostedUrl"),text=txt,remote=j.get("workplaceType")=="remote")
def norm_ashby(slug):
    d=get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    if not d or "jobs" not in d: return None
    for j in d["jobs"]:
        a=(j.get("address") or {}).get("postalAddress") or {}
        loc=", ".join(filter(None,[j.get("location"),a.get("addressRegion"),a.get("addressCountry")]))
        comp=((j.get("compensation") or {}).get("compensationTierSummary") or "").replace("–","-")
        yield dict(job_id=j["id"],company=slug,title=j.get("title"),location=loc,employment_type=j.get("employmentType"),department=j.get("department"),
            posted=(j.get("publishedAt") or "")[:10],url=j.get("jobUrl"),text=comp+" "+(j.get("descriptionPlain") or ""),remote=bool(j.get("isRemote")))
def norm_smartrecruiters(slug):
    off=0
    while True:
        d=get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={off}")
        if not d or not d.get("content"): return
        for j in d["content"]:
            l=j.get("location") or {}
            loc=", ".join(filter(None,[l.get("city"),l.get("region"),"USA" if l.get("country")=="us" else ("India" if l.get("country")=="in" else l.get("country"))]))
            yield dict(job_id=j["id"],company=(j.get("company") or {}).get("name") or slug,title=j.get("name"),location=loc,employment_type=(j.get("typeOfEmployment") or {}).get("label"),
                department=(j.get("department") or {}).get("label"),posted=(j.get("releasedDate") or "")[:10],url=f"https://jobs.smartrecruiters.com/{slug}/{j['id']}",text="",remote=bool(l.get("remote")))
        off+=100
        if off>=d.get("totalFound",0) or off>5000: return
NORM={"greenhouse":norm_greenhouse,"lever":norm_lever,"ashby":norm_ashby,"smartrecruiters":norm_smartrecruiters}
def crawl(ats,slug):
    try: rows=list(NORM[ats](slug) or [])
    except Exception as e: rows=None
    out=[];co=None;nus=nin=0
    for r in rows or []:
        c=country(r["location"]); fam,role=classify(r["title"]); co=r["company"]
        lo,hi,per=((salary(r["text"][-8000:]) if salary(r["text"][-8000:])[0] else salary(r["text"][:4000])) if c=="US" else (None,None,None))
        rem=int(bool(r.get("remote")) or bool(RE_REM.search(r["location"] or "")))
        keep=c in ("US","IN") and r["text"]
        nus+=c=="US"; nin+=c=="IN"
        out.append((ats,slug,r["job_id"],r["company"],r["title"],fam,role,r["location"],c,rem,r["employment_type"],r["department"],r["posted"],lo,hi,per,r["url"],
                    zlib.compress(r["text"][:30000].encode()) if keep else None,TODAY))
    with L:
        DB.executemany("INSERT OR REPLACE INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",out)
        DB.execute("INSERT OR REPLACE INTO boards VALUES(?,?,?,?,?,?,?,?)",(ats,slug,co,len(out),nus,nin,"ok" if rows is not None else "missing",TODAY))
        DB.commit()
    return len(out)
if __name__=="__main__":
    S=json.load(open(sys.argv[1] if len(sys.argv)>1 else "ats_slugs.json"))
    done={(a,s) for a,s in DB.execute("SELECT ats,slug FROM boards")}
    todo=[(a,s) for a,ss in S.items() if a in NORM for s in ss if (a,s) not in done]; random.shuffle(todo)
    print("boards todo",len(todo),flush=True); n=[0,0];t0=time.time()
    with cf.ThreadPoolExecutor(12) as ex:
        for k in ex.map(lambda x:crawl(*x),todo):
            n[0]+=1;n[1]+=k
            if n[0]%500==0: print(f"boards {n[0]}/{len(todo)} jobs {n[1]} {time.time()-t0:.0f}s",flush=True)
    print("DONE boards",n[0],"jobs",n[1])
