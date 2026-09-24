# US Job Market Engine

Which US jobs can be done from India? We wanted a real answer, not a hunch, so we built a small engine that reads the US job market and scores every role for how "offshorable" it is.

First run (September 2026):

- **849,000** US job postings from the last 90 days, across 65 remote-capable roles and 73,000 companies
- **428,000** jobs pulled straight from 8,200 company career pages, **89,000** of them with a posted salary
- **24,000** India jobs posted by those same companies, which shows where US companies already hire in India

This repo is the code. Clone it, point it at your own role list, and run it.

## What we found

Top 20 roles by opportunity (offshore score weighted by volume):

| Role | Offshore score | US postings (90d) | Contract % | Remote % | India ratio | US median pay |
|---|---|---|---|---|---|---|
| Software Engineer | 54 | 92,942 | 10.0% | 26.2% | 0.189 | $205K |
| SAP | 75 | 21,995 | 26.1% | 19.8% | 0.385 | $152K |
| Backend Developer | 75 | 21,170 | 32.0% | 27.9% | 0.29 | $207K |
| AI / LLM Engineer | 57 | 29,678 | 9.4% | 22.2% | 0.169 | $212K |
| Data Engineer | 58 | 28,544 | 13.0% | 22.8% | 0.182 | $182K |
| Product Owner / BA | 54 | 31,890 | 22.5% | 22.8% | 0.1 | $125K |
| Customer / Tech Support | 48 | 39,454 | 11.9% | 28.0% | 0.092 | $92K |
| Recruiter | 55 | 29,326 | 15.4% | 24.0% | 0.127 | $140K |
| Data Analyst | 57 | 22,375 | 14.8% | 33.6% | 0.125 | $135K |
| Full Stack Developer | 66 | 16,506 | 15.7% | 27.3% | 0.247 | $193K |
| Inside Sales | 40 | 44,082 | 5.2% | 36.1% | 0.018 | $75K |
| Cloud Engineer | 59 | 17,927 | 23.6% | 24.7% | 0.179 | $163K |
| QA / Test Engineer | 57 | 17,862 | 23.7% | 17.2% | 0.216 | $145K |
| Oracle | 64 | 13,313 | 26.2% | 21.7% | 0.207 | $142K |
| DevOps / SRE | 62 | 13,418 | 17.6% | 27.5% | 0.21 | $194K |
| FP&A / Financial Analyst | 43 | 26,666 | 8.2% | 16.5% | 0.075 | $131K |
| Salesforce | 69 | 10,248 | 24.3% | 27.8% | 0.248 | $161K |
| Operations Analyst | 44 | 24,911 | 7.9% | 18.5% | 0.067 | $120K |
| AP / AR Specialist | 44 | 23,491 | 16.1% | 15.2% | 0.04 | $70K |
| ServiceNow | 65 | 8,695 | 22.8% | 25.9% | 0.2 | $147K |
Full table for all 65 roles: [`examples/offshore_fit_2026-09.json`](examples/offshore_fit_2026-09.json)

A few things stood out:

1. **Enterprise apps are the proven market.** SAP, Oracle, Salesforce and ServiceNow roles are 23 to 26% contract, and US companies already post a large share of them in India.
2. **Back office is the most under-served.** AP/AR, payroll, recruiting and support have thousands of small buyers, but very few of them hire in India directly. The work still gets done in India, just through vendors.
3. **Backend engineering is already moving.** On company career pages, US companies post almost one India backend role for every US one.
4. **GTM engineering is the fastest-growing role we tracked** (+169% share of postings quarter on quarter), but it's still almost all full-time hiring.

## How it works

Three layers. Only the first one is required, and it's free.

**1. Career-page crawler (free).** Most tech and mid-market companies host jobs on Greenhouse, Lever, Ashby or SmartRecruiters, and all four have public job-board APIs. We find company boards through the [Common Crawl](https://commoncrawl.org) index, then pull every open job with its full description, location and posted pay range into SQLite.

**2. Market map (optional, needs a [Blitz](https://blitz-api.ai) key).** Count queries across the wider US market (mostly LinkedIn-sourced postings) for each role: volume, monthly trend, remote share, contract share, seniority, and how often US-headquartered companies post the same role in India or the Philippines.

**3. Offshore score (0 to 100).**

| Signal | Weight | Why |
|---|---|---|
| India ratio: India postings ÷ US postings at US-HQ companies | 35 | Revealed behaviour. Companies already doing it. |
| Remote share | 20 | The job already works without an office. |
| Contract share | 15 | Buyers already use contractors for it. |
| Not location-bound (no physical presence, licence or clearance) | 20 | Hard filter on what can move. |
| Growth | 10 | Where demand is heading. |

As a sanity check, nurses, truck drivers and retail staff score 2 to 8. Most digital roles score 50 to 86.

## Quickstart

```bash
git clone https://github.com/yc-droid/us-job-market-engine && cd us-job-market-engine/radar
pip install -r ../requirements.txt

python cc_slugs.py                  # find company job boards via Common Crawl -> ats_slugs.json
python ats_crawl.py ats_slugs.json  # crawl every board -> jobs.db (SQLite)
python analyze_ats.py               # role-level stats: volume, remote %, salary, India ratio

# optional: guess boards for your own company list
python guess_slugs.py my_companies.csv > guess_slugs.json && python ats_crawl.py guess_slugs.json

# optional: US market map + offshore score (needs Blitz)
export BLITZ_API_KEY=...
python market_map.py && python score.py
```

A full crawl of about 10,000 boards takes 15 to 20 minutes on a laptop. Edit `taxonomy.py` to change the role list.

## Files

| File | What it does |
|---|---|
| `radar/taxonomy.py` | 114 roles in 20 families: title keywords, exclusions, and a location-bound flag |
| `radar/cc_slugs.py` | Lists company boards from the Common Crawl CDX index |
| `radar/ats_crawl.py` | Crawler: Greenhouse, Lever, Ashby, SmartRecruiters. Parses location and salary. Resumable. |
| `radar/analyze_ats.py` | Role stats from the crawl |
| `radar/market_map.py`, `score.py` | Blitz market map and offshore score |
| `radar/blitz_bulk.py` | Pulls every posting for high-scoring roles, splitting queries to get past the 5K cap |
| `examples/` | Output from our September 2026 run (role-level stats only) |

## Limits

- The India ratio only counts US companies posting jobs in India directly. Work that reaches India through outsourcing vendors doesn't show up, so back office scores are understated.
- Career-page data leans toward tech and startups, which pushes salary medians up.
- Roles are matched on job titles, so there's some noise.
- Trends cover about 8 months.

## Good citizenship

Only public, documented job-board endpoints and Common Crawl. The crawler caps at 12 concurrent requests and backs off when rate-limited. No login walls, no LinkedIn scraping, and no personal data: jobs only, never people. Please keep it that way if you fork it.

## License

MIT. Built by [SalesUp](https://salesup.club). If you use it, tell us what you found.
