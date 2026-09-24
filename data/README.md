# Data (snapshot: 23 to 24 September 2026)

Everything the engine collected on its first run, ready to use.

## Files

| File | Rows | What it is |
|---|---|---|
| `jobs_2026-09.csv.gz` | 438,656 | Every open job on 8,296 company career pages (Greenhouse, Lever, Ashby, SmartRecruiters). 210K US, 25K India, 93K with a posted salary. |
| `boards_2026-09.csv` | 8,296 | One row per company board: open jobs, US jobs, India jobs. |
| `role_stats_career_pages_2026-09.json` | 118 roles | Per role from the career pages: US jobs, companies, remote %, salary p25/median/p75, India jobs, India to US ratio. |
| `market_map_counts_2026-09.json` | 103 roles | US job posting counts per role from the wider market (Blitz jobs index, mostly LinkedIn-sourced). Monthly volume for 9 months, remote, contract, seniority, and postings by US-HQ companies in the US, India and the Philippines. |

The offshore score per role is in [`../examples/offshore_fit_2026-09.json`](../examples/offshore_fit_2026-09.json).

## `jobs_2026-09.csv.gz` columns

| Column | Notes |
|---|---|
| `ats` | greenhouse, lever, ashby or smartrecruiters |
| `company_slug`, `company` | Board slug and company name as shown on the board |
| `title` | Job title |
| `family`, `role` | Our classification from `radar/taxonomy.py`. Title-keyword match, about 30% land in `Other`. |
| `location`, `country` | Raw location text, and our parse: US, IN or OTHER |
| `remote` | 1 if the board flags it remote or the location says remote |
| `employment_type`, `department` | As given by the board (often blank on Greenhouse) |
| `posted` | Date first published or last updated, as the board reports it |
| `salary_min`, `salary_max`, `salary_period` | Parsed from posted pay ranges on US jobs. `period` is year or hour. Blank if no range was posted. |
| `url` | Link to the original posting |
| `crawled` | Date we fetched it |

## Load it

```python
import pandas as pd
jobs = pd.read_csv("data/jobs_2026-09.csv.gz")
us = jobs[jobs.country == "US"]
us.groupby("role").salary_max.median().sort_values(ascending=False).head(20)
```

## Notes

- This is a snapshot. Jobs close and new ones open daily, so rerun `radar/ats_crawl.py` for fresh data.
- The sample leans toward tech, startups and mid-market companies, because those are the companies that use these job-board platforms. It is not the whole US labor market.
- Full job descriptions aren't included. Postings belong to the companies that wrote them, so follow the `url` for the full text. Email addresses in titles have been removed.
- The Blitz market map is shared as counts only. Raw rows from paid data providers aren't redistributed.

## License

Our compilation, classifications and counts are CC BY 4.0: use them for anything, just credit "US Job Market Engine by SalesUp". The job postings themselves belong to the companies that published them.
