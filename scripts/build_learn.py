"Build the learning site: 5 tracks, 24 courses, 912 lessons (zh + en)."
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_common as S

OUT = S.PROJECT / "cryptography-site-learn"
ASSETS = S.CORE / "shared"
DATA_DIR = S.CORE / "content" / "learn"
DATA_NAMES = ("course-meta.json", "quiz-data.json", "capstones.json", "course-games.json")


def copy_assets(extra_data=None):
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for name in ("main.css", "learn.css", "logo.svg", "icon-192.png", "icon-512.png"):
        shutil.copy2(ASSETS / name, OUT / "assets" / name)
    shutil.copy2(S.CORE / "scripts" / "assets" / "local-links.js", OUT / "assets" / "local-links.js")
    shutil.copy2(S.CORE / "scripts" / "assets" / "learn.js", OUT / "assets" / "learn.js")
    for name in DATA_NAMES:
        candidates = [DATA_DIR / name, (extra_data or Path()) / name, OUT / "assets" / name]
        for src in candidates:
            if src and src.exists():
                shutil.copy2(src, OUT / "assets" / name)
                break


def write(path: str, text: str):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def label(lang, zh, en):
    return zh if lang == "zh" else en


def level_label(lang, level):
    n = int(level or 2)
    return {"zh": f"层级 {n}", "en": f"Level {n}"}.get(lang, f"L{n}")


def track_counts(courses):
    out = {}
    for t in S.TRACKS:
        out[t["id"]] = sum(c["count"] for c in courses if c["track"] == t["id"])
    return out


def home(lang, entries, courses, article_by_entry, games_by_knowledge):
    zh = lang == "zh"
    counts = track_counts(courses)
    t = "学习站" if zh else "Learn"
    intro = (
        "把 912 条知识重新排成 5 条路线、24 门课。每一课都从主站的知识条目出发：先读一段，再回到完整条目，最后用游戏练一次。"
        if zh else
        "Reorder 912 knowledge entries into 5 tracks and 24 courses. Every lesson starts from a canonical entry on the main site, then points back to the full article and a game to practise."
    )
    body = f'''<section class="learn-hero"><div>
<p class="hero-eyebrow">LEARN · 学习站</p>
<h1>不是另一套百科，<br>而是<em>一条能走完的路</em></h1>
<p>{intro}</p>
<div class="hero-actions"><a class="button primary" href="{"/en/courses/d01-foundations/" if not zh else "/courses/d01-foundations/"}">从第一课开始 <span aria-hidden="true">→</span></a><a class="quiet-link" href="{S.PLAY}/">先去游戏里试试 <span aria-hidden="true">↗</span></a></div>
</div><div><div class="learn-stat-grid"><div class="learn-stat"><strong>912</strong><span>知识课时</span></div><div class="learn-stat"><strong>24</strong><span>技术域课程</span></div><div class="learn-stat"><strong>5</strong><span>宏观路线</span></div></div><p class="learn-note">课程页只给导读、目标与边界；完整定义、来源和计算回主站。学习记录保存在本机，并用 <code>.poyi.net</code> cookie 在三站之间共享。</p></div></section>'''

    body += '<section class="section"><div class="section-heading"><p class="eyebrow">FIVE TRACKS</p><h2>五条路线，先选一条走</h2><p>从古典到后量子，路线不是目录，而是依赖顺序。每条路线下是具体技术域课程。</p></div><div class="track-grid">'
    for tr in S.TRACKS:
        first = next(c for c in courses if c["track"] == tr["id"])
        href = f'/{"en/" if not zh else ""}courses/{first["id"]}/'
        body += f'''<a class="track-card {tr["color"]}" href="{href}"><span class="track-kicker">{tr["en"]}</span><h3>{tr["title"]}</h3><p>{tr["desc"]}</p><span class="track-meta"><span>{counts[tr["id"]]} 课时</span><span>{len(tr["domains"])} 门课 →</span></span></a>'''
    body += "</div></section>"

    body += '<section class="section"><div class="section-heading"><p class="eyebrow">COURSES</p><h2>二十四门技术域课程</h2><p>每门课按层级从低到高排列；跨域条目只落在它的第一技术域，避免重复计数。</p></div>'
    for tr in S.TRACKS:
        body += f'<div style="margin-top:30px"><p class="eyebrow">{tr["en"]}</p><h2 style="font-size:22px">{tr["title"]}</h2><div class="course-grid">'
        for c in [x for x in courses if x["track"] == tr["id"]]:
            href = f'/{"en/" if not zh else ""}courses/{c["id"]}/'
            body += f'''<a class="course-card {c["color"]}" href="{href}"><div class="course-top"><span class="course-code">{c["code"]}</span><span class="course-code">{c["count"]} lessons</span></div><h3>{c["title"] if zh else c["title_en"]}</h3><p class="course-en">{c["title_en"] if zh else c["title"]}</p><p>{c["desc"]}</p><div class="course-foot"><span>{c["track_title"]}</span><strong>进入课程 →</strong></div></a>'''
        body += "</div></div>"
    body += "</section>"

    # A small "start here" strip with four canonical entry examples.
    picks = []
    wanted = ["caesar-cipher", "machine--enigma", "algorithm--aes", "bb84"]
    by_id = {e["id"]: e for e in entries}
    for eid in wanted:
        if eid in by_id:
            picks.append(by_id[eid])
    body += '<section class="section"><div class="section-heading"><p class="eyebrow">START SMALL</p><h2>先读四条，再决定走哪条路</h2></div><div class="course-grid">'
    for e in picks:
        c = S.course_for_entry(courses, e["id"])
        href = f'/{"en/" if not zh else ""}lessons/{e["id"]}/'
        body += f'''<a class="course-card" href="{href}"><span class="course-code">{c["code"]} · {level_label(lang, e.get("level"))}</span><h3>{e["title"] if zh else e.get("title_en", e["title"])}</h3><p>{S.excerpt(S.article_text(article_by_entry.get(e["id"]), lang, "principle"), 150) or S.excerpt(e.get("note"), 150)}</p><div class="course-foot"><span>{c["title"]}</span><strong>读这一课 →</strong></div></a>'''
    body += "</div></section>"
    return body


def course_page(lang, c, art_by_entry):
    zh = lang == "zh"
    path = f'/{"en/" if not zh else ""}courses/{c["id"]}/'
    alt = f'{S.LEARN}/{"courses" if not zh else "en/courses"}/{c["id"]}/'
    rows = []
    for i, e in enumerate(c["entries"], 1):
        href = f'/{"en/" if not zh else ""}lessons/{e["id"]}/'
        title = e["title"] if zh else e.get("title_en", e["title"])
        summary = S.excerpt(S.article_text(art_by_entry.get(e["id"]), lang, "principle"), 90) or S.excerpt(e.get("note"), 90)
        rows.append(f'''<li class="lesson-row" data-lesson-id="{S.esc(e["id"])}"><span class="lesson-no">{i:03d}</span><div><h4><a href="{href}">{S.esc(title)}</a></h4><small>{S.esc(summary)}</small></div><span class="lesson-state">L{e.get("level", 2)} · 未读</span></li>''')
    body = f'''<div class="breadcrumbs"><a href="{"/en/" if not zh else "/"}">学习站</a><span>/</span><a href="{"/en/" if not zh else "/"}#courses">{c["track_title"]}</a><span>/</span><span>{c["title"]}</span></div>
<section class="course-head"><div><p class="eyebrow">{c["code"]} · {c["track_title"]}</p><h1>{c["title"] if zh else c["title_en"]}</h1><p class="course-en">{c["title_en"] if zh else c["title"]}</p><p>{c["desc"]}</p></div><aside class="course-progress-panel" data-course-progress data-course="{c["id"]}" data-total="{c["count"]}"><strong data-progress-count>0 / {c["count"]}</strong><span>已读课时 · 本机记录</span><div class="progress-track"><span data-progress-bar></span></div><p style="font-size:11px;color:var(--muted);line-height:1.7;margin-top:10px">点课时进入导读；读完后在课时页标记完成。进度会同步到 play 站的“已解锁”判断（后续接入）。</p></aside></section>
<section><ul class="lesson-list">{''.join(rows)}</ul></section>'''
    return S.page(site="learn", lang=lang, title=(c["title"] if zh else c["title_en"]), description=c["desc"], body=body, path=path, active="learn", alt_href=alt, extra_css="learn.css")


def lesson_page(lang, e, c, article, courses, game):
    zh = lang == "zh"
    eid = e["id"]
    path = f'/{"en/" if not zh else ""}lessons/{eid}/'
    alt = f'{S.LEARN}/{"lessons" if not zh else "en/lessons"}/{eid}/'
    title = e["title"] if zh else e.get("title_en", e["title"])
    domains = [S.load_domains().get(d, {}).get("title", d) for d in (e.get("domain") or [])]
    meta = [level_label(lang, e.get("level")), e.get("type", "term"), " · ".join(domains[:2]) if domains else ""]
    principle = S.article_text(article, lang, "principle") or e.get("note") or ""
    why = S.article_text(article, lang, "why")
    broken = S.article_text(article, lang, "broken")
    goal = (
        f"读完这一课，你能用自己的话解释「{title}」在密码学里解决什么问题、它依赖什么假设，以及至少一个会失效的边界。"
        if zh else
        f"By the end, you can explain what “{title}” solves, which assumption it relies on, and at least one boundary where it fails."
    )
    main_url = f'{S.MAIN}/{"en/" if not zh else ""}entries/{eid}/'
    body = f'''<div class="breadcrumbs"><a href="{"/en/" if not zh else "/"}">学习站</a><span>/</span><a href="{"/en/" if not zh else "/"}courses/{c["id"]}/">{c["title"] if zh else c["title_en"]}</a><span>/</span><span>{S.esc(title)}</span></div>
<div class="lesson-layout"><article class="lesson-main"><p class="eyebrow">{c["code"]} · {c["track_title"]}</p><h1>{S.esc(title)}</h1><div class="lesson-meta">{''.join(f'<span>{S.esc(x)}</span>' for x in meta if x)}</div>
<div class="lesson-goal"><h2>这一课要解决什么</h2><p>{S.esc(goal)}</p></div>
<p class="lesson-excerpt">{S.esc(S.excerpt(principle, 330))}</p>
<section class="lesson-body"><h2>为什么值得读</h2><p>{S.esc(S.excerpt(why or principle, 420))}</p><h2>边界与攻击面</h2><p>{S.esc(S.excerpt(broken or ("这一条的重点是把定义、假设和实现分开；不要把教学模型当成现实系统的安全证明。" if zh else "The point is to separate definition, assumption and implementation; a teaching model is not a security proof for a real system."), 420))}</p><p class="small">这是导读，不是全文。完整定义、来源、计算与图表在主站条目页。</p></section>
<div class="lesson-actions"><button class="mark-button" type="button" data-mark="{S.esc(eid)}" aria-pressed="false"><span data-mark-icon>○</span><span data-mark-text>标记已读</span></button><a class="button secondary" href="{main_url}">去主站读全文 ↗</a>{f'<a class="quiet-link" href="{S.PLAY}/game/{game["id"]}/">玩相关游戏 →</a>' if game else ''}</div>
<div class="lesson-pager">'''
    idx = next((i for i, x in enumerate(c["entries"]) if x["id"] == eid), 0)
    prev = c["entries"][idx - 1] if idx > 0 else None
    nxt = c["entries"][idx + 1] if idx + 1 < len(c["entries"]) else None
    if prev:
        body += f'<a href="/{"en/" if not zh else ""}lessons/{prev["id"]}/"><span>← 上一课</span><b>{S.esc(prev["title"] if zh else prev.get("title_en", prev["title"]))}</b></a>'
    else:
        body += '<span></span>'
    if nxt:
        body += f'<a href="/{"en/" if not zh else ""}lessons/{nxt["id"]}/"><span>下一课 →</span><b>{S.esc(nxt["title"] if zh else nxt.get("title_en", nxt["title"]))}</b></a>'
    else:
        body += '<span></span>'
    body += f'''</div></article><aside class="lesson-side" data-lesson-course data-course="{c["id"]}" data-total="{c["count"]}" data-lessons="{','.join(e['id'] for e in c['entries'])}"><div class="side-card"><h3>课程坐标</h3><p>{c["title"] if zh else c["title_en"]}</p><p style="margin-top:8px">{c["code"]} · 第 {idx + 1} / {c["count"]} 课</p><div style="margin-top:12px"><div class="progress-track"><span data-lesson-course-bar></span></div></div></div><div class="side-card"><h3>前置与关联</h3><ul>'''
    for pid in (e.get("prereq") or [])[:5]:
        p = next((x for x in courses for x in x["entries"] if x["id"] == pid), None)
        if p:
            body += f'<li><a href="/{"en/" if not zh else ""}lessons/{pid}/">{S.esc(p["title"] if zh else p.get("title_en", p["title"]))}</a></li>'
        else:
            body += f'<li>{S.esc(pid)}</li>'
    if not (e.get("prereq") or []):
        body += '<li>无显式前置；可以直接从这一课开始。</li>'
    body += f'''</ul></div><div class="side-card"><h3>换一种方式</h3><a class="side-link" href="{main_url}"><span>主站完整条目</span><span>↗</span></a>{f'<a class="side-link" href="{S.PLAY}/game/{game["id"]}/"><span>相关游戏</span><span>▶</span></a>' if game else ''}<a class="side-link" href="{"/en/" if not zh else "/"}courses/{c["id"]}/"><span>回到课程</span><span>←</span></a></div></aside></div>'''
    return S.page(site="learn", lang=lang, title=title, description=S.excerpt(principle, 150), body=body, path=path, active="learn", alt_href=alt, noindex=True, extra_css="learn.css")


def progress_page(lang, courses):
    zh = lang == "zh"
    body = '''<div class="breadcrumbs"><a href="/">学习站</a><span>/</span><span>学习记录</span></div><section class="course-head"><div><p class="eyebrow">PROGRESS</p><h1>学习记录</h1><p>所有标记只保存在本机；在 <code>*.poyi.net</code> 下会尝试写入同域 cookie，让主站、学习站和游戏站读到同一份进度。</p></div></section><div class="course-grid">'''
    for c in courses:
        body += f'''<div class="course-card" data-progress-card data-course="{c["id"]}" data-total="{c["count"]}" data-lessons="{','.join(e['id'] for e in c['entries'])}"><span class="course-code">{c["code"]} · {c["count"]} lessons</span><h3>{c["title"] if zh else c["title_en"]}</h3><p>{c["desc"]}</p><div class="course-foot"><span data-progress-count>0 / {c["count"]}</span><a href="{"/en/" if not zh else "/"}courses/{c["id"]}/">继续 →</a></div></div>'''
    body += "</div>"
    return S.page(site="learn", lang=lang, title="学习记录" if zh else "Progress", description="本机学习进度", body=body, path=f'/{"en/" if not zh else ""}progress/', active="learn", extra_css="learn.css", noindex=True)


def main():
    _, entries = S.load_catalog()
    domains = S.load_domains()
    articles = S.load_articles()
    art_by_entry, _ = S.article_index(articles)
    courses = S.build_courses(entries, domains)
    games = {}
    manifest = S.PROJECT / "cryptography-games" / "games-manifest.json"
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for g in payload.get("games", []):
            for kid in g.get("knowledgeIds", []):
                games.setdefault(kid, g)
    if OUT.exists():
        github_dir = None
        if (OUT / ".github").is_dir():
            github_dir = Path(tempfile.mkdtemp(prefix="learn-github-"))
            shutil.copytree(OUT / ".github", github_dir / ".github")
        stash = Path(tempfile.mkdtemp(prefix="learn-data-"))
        for name in DATA_NAMES:
            src = OUT / "assets" / name
            if src.exists():
                shutil.copy2(src, stash / name)
        shutil.rmtree(OUT)
    else:
        github_dir = None
        stash = Path(tempfile.mkdtemp(prefix="learn-data-"))
    OUT.mkdir(parents=True)
    if github_dir:
        shutil.copytree(github_dir / ".github", OUT / ".github")
    copy_assets(stash)
    for lang in ("zh", "en"):
        write(("" if lang == "zh" else "en/") + "index.html", S.page(site="learn", lang=lang, title=("学习站" if lang == "zh" else "Learn"), description="5 条路线、24 门课、912 个课时；从主站知识条目出发的密码学学习路径。", body=home(lang, entries, courses, art_by_entry, games), path=("/" if lang == "zh" else "/en/"), active="learn", alt_href=(S.LEARN + "/en/" if lang == "zh" else S.LEARN + "/"), extra_css="learn.css"))
        for c in courses:
            write(("" if lang == "zh" else "en/") + f'courses/{c["id"]}/index.html', course_page(lang, c, art_by_entry))
        for c in courses:
            for e in c["entries"]:
                write(("" if lang == "zh" else "en/") + f'lessons/{e["id"]}/index.html', lesson_page(lang, e, c, art_by_entry.get(e["id"]), courses, games.get(e["id"])))
        write(("" if lang == "zh" else "en/") + "progress/index.html", progress_page(lang, courses))
    # Search index for the learn site.
    idx = [{"id": e["id"], "title": e["title"], "title_en": e.get("title_en", e["title"]), "course": c["id"], "course_title": c["title"], "url": f'/lessons/{e["id"]}/', "url_en": f'/en/lessons/{e["id"]}/'} for c in courses for e in c["entries"]]
    write("search-index.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    paths = ["/", "/en/", "/progress/", "/en/progress/"] + [f'/courses/{c["id"]}/' for c in courses] + [f'/en/courses/{c["id"]}/' for c in courses]
    write("sitemap.xml", S.sitemap(S.LEARN, paths))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {S.LEARN}/sitemap.xml\n")
    write("CNAME", "learn.poyi.net\n")
    write(".nojekyll", "")
    write("404.html", S.page(site="learn", lang="zh", title="没有找到这一页", description="学习站 404", body='<div class="page-heading"><p class="eyebrow">404</p><h1>这一页不在路线里</h1><p>回到学习站首页，从 5 条路线或 24 门课重新进入。</p></div><div class="hero-actions"><a class="button primary" href="/">回到学习站</a><a class="quiet-link" href="' + S.MAIN + '/explore/">去主站探索 →</a></div>', path="/404.html", active="learn", extra_css="learn.css", noindex=True))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in DATA_NAMES:
        src = stash / name
        if src.exists() and not (DATA_DIR / name).exists():
            shutil.copy2(src, DATA_DIR / name)
    print(json.dumps({"courses": len(courses), "lessons": sum(c["count"] for c in courses), "pages": len(list(OUT.rglob('*.html'))), "data": len(list(DATA_DIR.glob('*.json'))), "stash": str(stash)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
