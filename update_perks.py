#!/usr/bin/env python3
"""Scrape the Dead by Daylight wiki for the current perk list and write dbd-perks.json.

Usage:
    python update_perks.py

Then in the randomiser, click "Import Perks" and select the generated dbd-perks.json.
"""
import re, json, html, urllib.request

URL = "https://deadbydaylight.wiki.gg/wiki/Perks"
OUT = "dbd-perks.json"

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://deadbydaylight.wiki.gg/",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def scrape():
    page = fetch(URL)
    # locate section boundaries by id
    surv_idx = page.find('id="Survivor_Perks_(179)"')
    kill_idx = page.find('id="Killer_Perks_(151)"')
    # survivor section: from surv_idx to kill_idx
    # killer section: from kill_idx to end (or next major heading)
    sections = {
        "survivor": page[surv_idx:kill_idx],
        "killer": page[kill_idx:],
    }
    out = {"killer": [], "survivor": []}
    seen = {"killer": set(), "survivor": set()}
    for role, chunk in sections.items():
        for tr in re.findall(r'<tr>(.*?)</tr>', chunk, re.S):
            # icon
            im = re.search(r'<img[^>]*src="(/images/thumb/[^"]+?96px-[^"]+)"', tr)
            if not im:
                continue
            icon_rel = im.group(1)
            if 'Perk' not in icon_rel:
                continue
            # name: second <th> contains the perk name link
            ths = re.findall(r'<th[^>]*>(.*?)</th>', tr, re.S)
            name = None
            if len(ths) >= 2:
                nm = re.search(r'<a[^>]*>([^<]+)</a>', ths[1], re.S)
                if nm:
                    name = html.unescape(nm.group(1).strip())
            if not name or name in seen[role]:
                continue
            # description: first <td> content
            td = re.search(r'<td[^>]*>(.*?)</td>', tr, re.S)
            desc = strip_tags(td.group(1)) if td else ""
            # skip header/empty rows
            if not desc or len(desc) < 10:
                continue
            seen[role].add(name)
            out[role].append({
                "name": name,
                "icon": "https://deadbydaylight.wiki.gg" + icon_rel,
                "desc": desc,
            })
    return out

if __name__ == "__main__":
    data = scrape()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT}: {len(data['killer'])} killer, {len(data['survivor'])} survivor perks")
PY