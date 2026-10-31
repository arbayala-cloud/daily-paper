#!/usr/bin/env python3
"""Daily Paper generator. Free RSS only (no keys). Usage:
  python3 build.py            # refresh RSS sections -> data.json
  python3 build.py --x FILE   # also rebuild From X section from an X search result file -> x.json
"""
import json, re, sys, html, urllib.request, urllib.parse, datetime, email.utils
from zoneinfo import ZoneInfo
CT = ZoneInfo("America/Chicago")
def gn(q): return "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:2d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
SECTIONS = {
 "Top US News": [("NPR", "https://feeds.npr.org/1001/rss.xml"), ("NPR National", "https://feeds.npr.org/1003/rss.xml"),
                 ("AP", gn("site:apnews.com")), ("BBC US", "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml")],
 "Texas": [("WFAA", "https://www.wfaa.com/feeds/syndication/rss/news"), ("NBC DFW", "https://www.nbcdfw.com/feed/"),
           ("Fox 4", "https://www.fox4news.com/rss/category/news"), ("Star-Telegram", gn("site:star-telegram.com")),
           ("Texas Tribune", gn("site:texastribune.org"))],
 "Vermont": [("VTDigger", gn("site:vtdigger.org")), ("WCAX", "https://www.wcax.com/arc/outboundfeeds/rss/?outputType=xml"),
             ("Burlington Free Press", gn("site:burlingtonfreepress.com")), ("St. Albans Messenger", "https://www.samessenger.com/search/?f=rss")],
 "Crime": [("US", gn("crime OR arrested OR shooting OR murder")), ("Texas", gn("(Fort Worth OR Dallas OR Texas) (police OR arrested OR shooting OR crime)")),
           ("Vermont", gn("Vermont (police OR arrested OR crime OR charged)"))],
}
PER_FEED, PER_SECTION = 6, 18
def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(s or "")))
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:177] + "...") if len(s) > 180 else s
def tag(block, t):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (t, t), block, re.S)
    return re.sub(r"^<!\[CDATA\[|\]\]>$", "", m.group(1).strip()) if m else ""
def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 DailyPaper"})
    xml = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    out = []
    for b in re.findall(r"<item[\s>](.*?)</item>", xml, re.S)[:PER_FEED]:
        title, link = clean(tag(b, "title")), tag(b, "link").strip()
        src = clean(tag(b, "source")) or name
        if "news.google.com" in url and " - " in title: title = title.rsplit(" - ", 1)[0]
        summ = clean(tag(b, "description"))
        if "news.google.com" in url or summ.startswith(title[:40]): summ = ""
        try: ts = email.utils.parsedate_to_datetime(tag(b, "pubDate")).timestamp()
        except Exception: ts = 0
        if title and link: out.append({"title": title, "source": src, "link": link, "summary": summ, "ts": ts})
    return out
def ct(ts): return datetime.datetime.fromtimestamp(ts, CT).strftime("%b %-d, %-I:%M %p CT") if ts else ""
def main():
    data = {"updated": datetime.datetime.now(CT).strftime("%A, %B %-d, %Y %-I:%M %p CT"), "sections": []}
    for sec, feeds in SECTIONS.items():
        items, seen = [], set()
        for name, url in feeds:
            try: got = fetch(name, url)
            except Exception as e: print("skip", name, e); got = []
            for it in got:
                k = it["title"].lower()[:60]
                if k not in seen: seen.add(k); items.append(it)
        items.sort(key=lambda i: -i["ts"])
        for i in items: i["time"] = ct(i["ts"])
        data["sections"].append({"name": sec, "items": items[:PER_SECTION]})
    json.dump(data, open("data.json", "w"), indent=1)
    if "--x" in sys.argv:
        raw = open(sys.argv[sys.argv.index("--x") + 1]).read()
        j = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        users = {u["id"]: u for u in j.get("includes", {}).get("users", [])}
        posts = []
        for p in j.get("data", []):
            u = users.get(p.get("author_id"), {})
            t = re.sub(r"https://t\.co/\S+|[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F]", "", p["text"]).strip()
            ts = datetime.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")).timestamp()
            posts.append({"title": clean(t), "source": "%s (@%s)" % (u.get("name", ""), u.get("username", "")), "link": p["url"], "summary": "", "ts": ts, "time": ct(ts)})
        json.dump({"updated": data["updated"], "items": posts}, open("x.json", "w"), indent=1)
    print("ok", [(s["name"], len(s["items"])) for s in data["sections"]])
if __name__ == "__main__": main()
