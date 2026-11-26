"Copy the knowledge build into the main release repo and turn it into the three-site hub."
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_common as S

SRC = S.PROJECT / "cryptography-decode-history" / "build" / "knowledge-site"
OUT = S.PROJECT / "cryptography-site-main"
SHARED = S.CORE / "shared"


def root_of(text):
    m = re.search(r'<html[^>]*data-root="([^"]*)"', text)
    return m.group(1) if m else "./"


def nav_html(root, lang):
    items = [
        (root + "explore/", "知识" if lang == "zh" else "Knowledge"),
        (root + "views/timeline/", "时代" if lang == "zh" else "Timeline"),
        (S.LEARN + "/", "学习" if lang == "zh" else "Learn"),
        (S.PLAY + "/", "游戏" if lang == "zh" else "Play"),
        (root + "about/", "关于" if lang == "zh" else "About"),
    ]
    return '<nav class="desktop-nav" aria-label="主导航">' + "".join(f'<a href="{u}">{t}</a>' for u, t in items) + "</nav>"


def bottom_html(root, lang):
    items = [
        (root, "⌂", "首页" if lang == "zh" else "Home"),
        (root + "explore/", "◎", "探索" if lang == "zh" else "Explore"),
        (S.LEARN + "/", "▤", "学习" if lang == "zh" else "Learn"),
        (S.PLAY + "/", "▶", "游戏" if lang == "zh" else "Play"),
    ]
    links = "".join(f'<a href="{u}"><span aria-hidden="true">{i}</span><span>{t}</span></a>' for u, i, t in items)
    return f'<nav class="bottom-nav" aria-label="移动导航">{links}<button type="button" data-settings><span aria-hidden="true">⚙</span><span>{"设置" if lang == "zh" else "Settings"}</span></button></nav>'


def footer_html(root, lang):
    return f'''<div class="footer-links"><a href="{S.MAIN}/">{"主站" if lang == "zh" else "Main"}</a><a href="{S.LEARN}/">{"学习站" if lang == "zh" else "Learn"}</a><a href="{S.PLAY}/">{"游戏站" if lang == "zh" else "Play"}</a><a href="{S.GITHUB_CONTENT}" target="_blank" rel="noopener noreferrer">{"内容仓" if lang == "zh" else "Content"} ↗</a><a href="{S.GITHUB_GAMES}" target="_blank" rel="noopener noreferrer">{"游戏仓" if lang == "zh" else "Games"} ↗</a><span>{"内容 CC BY 4.0 · 脚本 MIT" if lang == "zh" else "Content CC BY 4.0 · Code MIT"}</span></div>'''


def footer_note(lang):
    return ('一个站，三种走法：在知识里查清楚，在课程里走一遍，在游戏里练一次。' if lang == "zh" else
            'One site, three ways in: look it up, walk the course, then play it once.')


def hero_actions(lang):
    if lang == "zh":
        return f'''<div class="hero-actions"><a class="button primary" href="./explore/">开始探索 <span aria-hidden="true">→</span></a><a class="button secondary" href="{S.LEARN}/">去学习站</a><a class="quiet-link" href="{S.PLAY}/">玩游戏 →</a></div>'''
    return f'''<div class="hero-actions"><a class="button primary" href="../explore/">Start exploring <span aria-hidden="true">→</span></a><a class="button secondary" href="{S.LEARN}/en/">Go to Learn</a><a class="quiet-link" href="{S.PLAY}/">Play →</a></div>'''


def three_door(lang):
    if lang == "zh":
        cards = [
            ("KNOWLEDGE", "先查清楚", "912 条知识、927 篇专题；这里是正文与来源。", S.MAIN + "/explore/"),
            ("LEARN", "再走一遍", "5 条路线、24 门课、912 个课时；从导读回到全文。", S.LEARN + "/"),
            ("PLAY", "最后练一次", "119 款游戏，从凯撒到后量子；打开即玩。", S.PLAY + "/"),
        ]
        head = "三条路，随便从哪条进"
    else:
        cards = [
            ("KNOWLEDGE", "Look it up", "912 entries and 927 articles; canonical text and sources.", S.MAIN + "/en/explore/"),
            ("LEARN", "Walk the course", "5 tracks, 24 courses, 912 lessons; excerpts lead back to the full text.", S.LEARN + "/en/"),
            ("PLAY", "Play it once", "119 games, from Caesar to post-quantum; open and play.", S.PLAY + "/"),
        ]
        head = "Three ways in. Pick one."
    return f'''<section class="section" id="three-sites" style="padding-top:38px"><div class="section-heading"><p class="eyebrow">ONE SITE · THREE MODES</p><h2>{head}</h2><p>{"知识是正文，学习是路线，游戏是练习。" if lang == "zh" else "Knowledge is the text, learning is the route, play is the practice."}</p></div><div class="three-door">''' + "".join(
        f'<a href="{u}"><span class="door-kicker">{k}</span><h3>{t}</h3><p>{d}</p><span class="door-arrow">{"进入 →" if lang == "zh" else "Enter →"}</span></a>'
        for k, t, d, u in cards
    ) + "</div></section>"


def process(text, lang, is_home):
    root = root_of(text)
    # Remove the old preview strip entirely.
    text = re.sub(r'<div class="preview-strip">.*?</div>', '', text, count=1, flags=re.S)
    # Replace desktop navigation.
    text = re.sub(r'<nav class="desktop-nav".*?</nav>', nav_html(root, lang), text, count=1, flags=re.S)
    # Replace footer links and note.
    text = re.sub(r'<div class="footer-links">.*?</div>', footer_html(root, lang), text, count=1, flags=re.S)
    text = re.sub(r'<p class="footer-note">.*?</p>', f'<p class="footer-note">{footer_note(lang)}<span aria-hidden="true">✦</span></p>', text, count=1, flags=re.S)
    # Replace the mobile nav with five entries.
    text = re.sub(r'<nav class="bottom-nav".*?</nav>', bottom_html(root, lang), text, count=1, flags=re.S)
    # Add the shared three-site CSS and local link rewriter once.
    if 'assets/three-site.css' not in text:
        text = text.replace('</head>', f'<link rel="stylesheet" href="{root}assets/three-site.css"></head>', 1)
    if 'assets/local-links.js' not in text:
        text = text.replace('</body>', f'<script src="{root}assets/local-links.js" defer></script></body>', 1)
    # Old domain references in copy.
    text = text.replace("game.poyi.net", "play.poyi.net").replace("crypto.poyi.net", "poyi.net")
    if is_home:
        text = re.sub(r'<div class="hero-actions">.*?</div>', hero_actions(lang), text, count=1, flags=re.S)
        marker = '</section><section class="section" id="explore">'
        if marker in text:
            text = text.replace(marker, '</section>' + three_door(lang) + '<section class="section" id="explore">', 1)
    return text


def write_404():
    css = next(OUT.glob("assets/site.*.css"), None)
    css_name = css.name if css else "site.css"
    body = f'''<div class="page-heading"><p class="eyebrow">404</p><h1>这一页不在探索馆里</h1><p>可能是旧链接，也可能是我们还没写到这里。回到主站目录，或去学习站、游戏站换一条路。</p></div><div class="hero-actions"><a class="button primary" href="{S.MAIN}/explore/">回主站探索</a><a class="button secondary" href="{S.LEARN}/">去学习站</a><a class="quiet-link" href="{S.PLAY}/">去游戏站 →</a></div>'''
    header = S.nav("knowledge", "zh", None)
    html_doc = f'''<!doctype html><html lang="zh-CN" data-site="main"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><meta name="color-scheme" content="light dark"><title>没有找到这一页 · {S.SITE_NAME}</title><link rel="icon" type="image/svg+xml" href="/assets/logo.svg"><link rel="stylesheet" href="/assets/{css_name}"><link rel="stylesheet" href="/assets/three-site.css"></head><body><a class="skip-link" href="#main">跳到正文</a>{header}<main id="main" class="document-main">{body}</main>{S.footer("zh")}{S.bottom_nav("knowledge", "zh")}<script src="/assets/local-links.js" defer></script></body></html>'''
    (OUT / "404.html").write_text(html_doc, encoding="utf-8")


def main():
    if not SRC.exists():
        raise SystemExit("main build missing")
    github_dir = None
    if (OUT / ".github").is_dir():
        github_dir = Path(tempfile.mkdtemp(prefix="main-github-"))
        shutil.copytree(OUT / ".github", github_dir / ".github")
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    if github_dir:
        shutil.copytree(github_dir / ".github", OUT / ".github")
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("three-site.css",):
        shutil.copy2(SHARED / name, OUT / "assets" / name)
    shutil.copy2(S.CORE / "scripts" / "assets" / "local-links.js", OUT / "assets" / "local-links.js")
    count = 0
    for p in OUT.rglob("*.html"):
        rel = p.relative_to(OUT).as_posix()
        lang = "en" if rel.startswith("en/") else "zh"
        is_home = rel in ("index.html", "en/index.html")
        p.write_text(process(p.read_text(encoding="utf-8"), lang, is_home), encoding="utf-8")
        count += 1
    write_404()
    (OUT / "CNAME").write_text("poyi.net\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # Preserve the knowledge sitemap but ensure the root is canonical.
    meta = json.loads((SRC / "build-meta.json").read_text(encoding="utf-8")) if (SRC / "build-meta.json").exists() else {}
    meta.update({"site": "main", "domain": "poyi.net", "pages": count, "threeSites": True})
    (OUT / "site-build.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pages": count, "files": len(list(OUT.rglob('*'))), "html": count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
