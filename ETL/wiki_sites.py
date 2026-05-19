import requests
import pandas as pd
import time
import sqlalchemy as sa
import settings as s

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "WorldDataAtlas/1.0 (" + s.mail + ")"})

def get_wikipedia_sites():
    url = "https://www.mediawiki.org/w/api.php"
    params = {"action": "sitematrix", "format": "json"}
    response = SESSION.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    sites = []
    for key, value in data["sitematrix"].items():
        if key == "count": continue
        if not isinstance(value, dict): continue
        lang_code = value.get("code")
        lang_name = value.get("name")
        for site in value.get("site", []):
            if site.get("code") == "wiki":
                sites.append({
                    "language_code": lang_code,
                    "language_name": lang_name,
                    "wiki_url": site.get("url"),
                    "dbname": site.get("dbname")
                })
    return sites

def get_wiki_statistics(wiki_url):
    api_url = f"{wiki_url}/w/api.php"
    params = {
        "action": "query",
        "meta": "siteinfo",
        "siprop": "statistics",
        "format": "json"
    }
    response = SESSION.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["query"]["statistics"]

sites = get_wikipedia_sites()
rows, count = [], 0
print(len(sites))
print('____________')
for site in sites:
    try:
        stats = get_wiki_statistics(site["wiki_url"])
        count = count + 1
        print(count)
        rows.append({
            **site,
            "pages": stats.get("pages"),
            "articles": stats.get("articles"),
            "edits": stats.get("edits"),
            "images": stats.get("images"),
            "users": stats.get("users"),
            "active_users": stats.get("activeusers"),
            "admins": stats.get("admins"),
        })
        time.sleep(0.1)
    except Exception as e: print(f"Error for {site['wiki_url']}: {e}")
df = pd.DataFrame(rows)

engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE wiki.sites"))
df.to_sql(name="sites", schema="wiki", con=engine, if_exists="append", index=False, chunksize=25)

"""
CREATE TABLE wiki.languages (
    id INT IDENTITY(1,1) PRIMARY KEY,
    language_name NVARCHAR(255) NOT NULL,
    iso639_1 NVARCHAR(2),
    iso639_3 NVARCHAR(3),
    speakers BIGINT,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);    
"""