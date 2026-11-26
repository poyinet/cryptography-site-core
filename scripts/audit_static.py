#!/usr/bin/env python3
"""Static three-site audit: links, canonical, sitemap, robots and old-domain leakage.

Run from the project root:
    python cryptography-site-core/scripts/audit_static.py

Exit code 0 = no blockers, 1 = at least one error.  External HTTP checks are
intentionally out of scope; pair this with preview-new-site/serve_three.py and
scripts/check_http.py for a real browser/HTTP pass.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[2]
SITES = {
    "main": {"root": PROJECT / "cryptography-site-main", "host": "poyi.net"},
    "learn": {"root": PROJECT / "cryptography-site-learn", "host": "learn.poyi.net"},
    "play": {"root": PROJECT / "cryptography-site-play", "host": "play.poyi.net"},
}
OLD_HOSTS = ("www.poyi.net", "game.poyi.net", "crypto.poyi.net")
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "blob:", "ftp:")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.canonicals: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "a" and a.get("href"):
            self.links.append(("a", a["href"]))
        elif tag in ("script", "img", "iframe", "source", "video", "audio") and a.get("src"):
            self.links.append((tag, a["src"]))
        elif tag == "link":
            rel = (a.get("rel") or "").lower().split()
            if "canonical" in rel and a.get("href"):
                self.canonicals.append(a["href"])
            elif "stylesheet" in rel and a.get("href"):
                self.links.append(("css", a["href"]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def route_for(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def build_site(root: Path):
    pages: dict[str, Path] = {}
    exact: set[str] = {"/"}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        exact.add("/" + rel)
        if f.suffix.lower() == ".html":
            route = route_for(rel)
            pages[route] = f
            exact.add(route)
            if rel.endswith("/index.html"):
                exact.add("/" + rel)
    return pages, exact


def normalize(target: str, base_route: str) -> str:
    target = unquote(target.strip())
    target = target.split("#", 1)[0]
    target = target.split("?", 1)[0]
    if not target:
        return ""
    if target.startswith("//"):
        target = "https:" + target
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return target
    if not target.startswith("/"):
        target = posixpath.join(posixpath.dirname(base_route.rstrip("/")) or "/", target)
    target = posixpath.normpath(target)
    trail = target.endswith("/")
    if target != "/" and not trail and not posixpath.splitext(target)[1]:
        pass
    return target + ("/" if trail and not target.endswith("/") else "")


def target_exists(path: str, exact: set[str], pages: dict[str, Path]) -> bool:
    if not path:
        return True
    if path in exact or path in pages:
        return True
    if path.endswith("/") and (path + "index.html") in exact:
        return True
    if not path.endswith("/") and (path + "/") in pages:
        return True
    if not path.endswith("/") and (path + ".html") in exact:
        return True
    return False


def scan_site(name: str, root: Path, host: str, max_report: int):
    pages, exact = build_site(root)
    errors, warnings = [], []
    missing_links = []
    missing_canonical = []
    canonical_mismatch = []
    canonical_alias = []
    old_hits = []
    sitemap_issues = []
    sitemap_urls = []

    if not (root / "404.html").is_file():
        errors.append("missing 404.html")
    robots = root / "robots.txt"
    if not robots.is_file():
        errors.append("missing robots.txt")
    else:
        text = robots.read_text(encoding="utf-8", errors="ignore")
        if f"Sitemap: https://{host}/sitemap.xml" not in text.replace("http://", "https://"):
            warnings.append("robots.txt does not point at https://%s/sitemap.xml" % host)

    sitemap = root / "sitemap.xml"
    if not sitemap.is_file():
        warnings.append("missing sitemap.xml")
    else:
        try:
            tree = ET.parse(sitemap)
            for node in tree.iter():
                if node.tag.endswith("loc") and node.text:
                    sitemap_urls.append(node.text.strip())
        except Exception as exc:
            errors.append("sitemap parse failed: %s" % exc)
        seen = set()
        for loc in sitemap_urls:
            if loc in seen:
                sitemap_issues.append((loc, "duplicate"))
            seen.add(loc)
            u = urlsplit(loc)
            if u.scheme != "https" or u.netloc != host:
                sitemap_issues.append((loc, "wrong host"))
                continue
            path = normalize(u.path, "/")
            if not target_exists(path, exact, pages):
                sitemap_issues.append((loc, "not built"))

    for route, file in pages.items():
        if route == "/404.html":
            continue
        parser = PageParser()
        try:
            parser.feed(file.read_text(encoding="utf-8", errors="ignore"))
        except Exception as exc:
            errors.append("%s parse failed: %s" % (route, exc))
            continue
        raw = file.read_text(encoding="utf-8", errors="ignore")
        for old in OLD_HOSTS:
            if old in raw:
                old_hits.append((route, old))
                break
        if len(parser.canonicals) != 1:
            missing_canonical.append((route, len(parser.canonicals)))
        else:
            c = parser.canonicals[0].strip()
            expected = "https://%s%s" % (host, route)
            if c != expected:
                cu = urlsplit(c)
                target = normalize(cu.path, "/")
                if cu.netloc == host and target_exists(target, exact, pages):
                    canonical_alias.append((route, c))
                else:
                    canonical_mismatch.append((route, c, expected))
        for kind, target in parser.links:
            if not target or target.startswith("#"):
                continue
            low = target.strip().lower()
            if low.startswith(SKIP_SCHEMES):
                continue
            resolved = normalize(target, route)
            if not resolved:
                continue
            u = urlsplit(resolved)
            if u.scheme and u.scheme not in ("http", "https"):
                continue
            if u.netloc:
                peer = next((s for s, cfg in SITES.items() if cfg["host"] == u.netloc), None)
                if peer is None:
                    continue
                try:
                    peer_pages, peer_exact = build_site(SITES[peer]["root"])
                except Exception:
                    peer_pages, peer_exact = {}, set()
                if not target_exists(normalize(u.path, "/"), peer_exact, peer_pages):
                    missing_links.append((route, kind, resolved, "peer:" + peer))
                continue
            if not target_exists(normalize(u.path, "/"), exact, pages):
                missing_links.append((route, kind, resolved, "local"))

    summary = {
        "site": name,
        "host": host,
        "root": str(root),
        "html_pages": len(pages),
        "exact_paths": len(exact),
        "sitemap_urls": len(sitemap_urls),
        "missing_links": len(missing_links),
        "missing_canonical": len(missing_canonical),
        "canonical_alias": len(canonical_alias),
        "canonical_mismatch": len(canonical_mismatch),
        "sitemap_issues": len(sitemap_issues),
        "old_domain_hits": len(old_hits),
        "errors": errors,
        "warnings": warnings,
    }
    return {
        "summary": summary,
        "missing_links": missing_links[:max_report],
        "missing_canonical": missing_canonical[:max_report],
        "canonical_alias": canonical_alias[:max_report],
        "canonical_mismatch": canonical_mismatch[:max_report],
        "sitemap_issues": sitemap_issues[:max_report],
        "old_domain_hits": old_hits[:max_report],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=["all", "main", "learn", "play"], default="all")
    ap.add_argument("--out", default=str(PROJECT / "audit" / "static-audit.json"))
    ap.add_argument("--max-report", type=int, default=40)
    args = ap.parse_args()
    names = list(SITES) if args.site == "all" else [args.site]
    reports = {}
    blockers = 0
    for name in names:
        cfg = SITES[name]
        if not cfg["root"].is_dir():
            print("MISSING SITE ROOT: %s (%s)" % (name, cfg["root"]), file=sys.stderr)
            blockers += 1
            continue
        rep = scan_site(name, cfg["root"], cfg["host"], args.max_report)
        reports[name] = rep
        s = rep["summary"]
        print(
            "%-6s pages=%-6d sitemap=%-5d links_missing=%-5d canonical_missing=%-4d canonical_alias=%-4d canonical_bad=%-4d sitemap_bad=%-4d old_domain=%-4d"
            % (
                name,
                s["html_pages"],
                s["sitemap_urls"],
                s["missing_links"],
                s["missing_canonical"],
                s["canonical_alias"],
                s["canonical_mismatch"],
                s["sitemap_issues"],
                s["old_domain_hits"],
            )
        )
        blockers += sum(
            s[k] for k in ("missing_links", "missing_canonical", "canonical_mismatch", "sitemap_issues", "old_domain_hits")
        ) + len(s["errors"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"), "reports": reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("report: %s" % out)
    if blockers:
        print("BLOCKERS: %d — fix before publishing." % blockers, file=sys.stderr)
        return 1
    print("STATIC AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
