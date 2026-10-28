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

def upload_to_github(path):
    import os, base64
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set; skipping upload. Set it to auto-upload dbd-perks.json.")
        return
    USER = "KablHamm"
    REPO = "DBD-Perk-Randomiser"
    FN = "dbd-perks.json"
    def api(method, url, data=None):
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "update_perks"}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try: err = json.loads(e.read().decode("utf-8"))
            except: err = e.read().decode("utf-8", "replace")
            return e.code, err
    content = open(path, "rb").read()
    b64 = base64.b64encode(content).decode("ascii")
    status, resp = api("GET", f"https://api.github.com/repos/{USER}/{REPO}/contents/{FN}")
    sha = resp.get("sha") if status == 200 else None
    payload = {"message": f"Update {FN}", "content": b64, "branch": "main"}
    if sha:
        payload["sha"] = sha
    status, resp = api("PUT", f"https://api.github.com/repos/{USER}/{REPO}/contents/{FN}", payload)
    if status in (200, 201):
        print(f"Uploaded {FN} to GitHub.")
    else:
        print(f"Upload failed: {status} {resp}")

if __name__ == "__main__":
    data = scrape()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT}: {len(data['killer'])} killer, {len(data['survivor'])} survivor perks")
    upload_to_github(OUT)
PY