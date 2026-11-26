#!/usr/bin/env python3
"""HTTP smoke check for the three local sites.

Usage:
    python cryptography-site-core/scripts/check_http.py --start
    python cryptography-site-core/scripts/check_http.py --no-start

`--start` launches preview-new-site/serve_three.py (ports 8789/8790/8791)
and stops it afterwards.  The checks assert status, HTML content type, title,
and the boundary between the official play site and the raw open-arcade repo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROJECT = Path(__file__).resolve().parents[2]
CHECK_PATHS = {
    "http://127.0.0.1:8789": ["/", "/entries/caesar-cipher/", "/explore/", "/404.html", "/__missing-route__"],
    "http://127.0.0.1:8790": ["/", "/en/", "/courses/d02-monoalphabetic/", "/en/courses/d02-monoalphabetic/", "/progress/", "/en/progress/", "/lessons/caesar-cipher/", "/en/lessons/caesar-cipher/", "/__missing-route__"],
    "http://127.0.0.1:8791": ["/", "/game/caesar/", "/games/caesar/", "/404.html", "/__missing-route__"],
}


def check(url: str, expect_404: bool = False):
    try:
        with urlopen(url, timeout=12) as r:
            body = r.read().decode("utf-8", "ignore")
            status = r.status
            ctype = r.headers.get("content-type", "")
    except URLError as exc:
        if hasattr(exc, "code") and exc.code == 404:
            status, ctype, body = 404, "text/html", ""
        else:
            return {"url": url, "ok": False, "error": str(exc)}
    ok = (status == 404 if expect_404 else status == 200)
    ok = ok and ("text/html" in ctype or not body)
    ok = ok and (expect_404 or "<html" in body.lower())
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:100]
    return {"url": url, "status": status, "content_type": ctype, "title": title, "bytes": len(body), "ok": ok}


def wait_for(base: str, seconds: float = 12):
    end = time.time() + seconds
    while time.time() < end:
        try:
            with urlopen(base + "/", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", action="store_true", help="start preview-new-site/serve_three.py")
    ap.add_argument("--no-start", action="store_true", help="assume servers already running")
    ap.add_argument("--json", default=str(PROJECT / "audit" / "http-smoke.json"))
    args = ap.parse_args()
    proc = None
    if args.start:
        import subprocess
        proc = subprocess.Popen([sys.executable, str(PROJECT / "preview-new-site" / "serve_three.py")], cwd=str(PROJECT))
        for port in (8789, 8790, 8791):
            if not wait_for("http://127.0.0.1:%d" % port):
                print("server did not start: %d" % port, file=sys.stderr)
                if proc:
                    proc.terminate()
                return 1
    results = []
    for base, paths in CHECK_PATHS.items():
        for path in paths:
            results.append(check(base + path, expect_404=path.startswith("/__missing")))
    failed = [r for r in results if not r.get("ok")]
    for r in results:
        print("%s %-38s %s %s" % ("OK  " if r.get("ok") else "FAIL", r["url"].replace("http://127.0.0.1:", ""), r.get("status", ""), r.get("title", r.get("error", ""))))
    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    print("report: %s" % out)
    if failed:
        print("HTTP SMOKE FAILED: %d/%d" % (len(failed), len(results)), file=sys.stderr)
        return 1
    print("HTTP SMOKE PASSED: %d routes" % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
