# Turn a CSV of company names/domains into candidate ATS board slugs. Usage: python guess_slugs.py companies.csv > guess_slugs.json
import csv, re, json, sys
names=set()
for r in csv.DictReader(open(sys.argv[1])):
    for k in ("company","company_name","name","domain"):
        if r.get(k): names.add(r[k].split(".")[0] if k=="domain" else r[k])
c=set()
for n in names:
    n=re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|technologies|labs|group)\b\.?","",n.lower().strip())
    for s in {re.sub(r"[^a-z0-9]","",n),re.sub(r"[^a-z0-9]+","-",n).strip("-")}:
        if 2<len(s)<50: c.add(s)
json.dump({a:sorted(c) for a in ["greenhouse","lever","ashby"]},sys.stdout)
