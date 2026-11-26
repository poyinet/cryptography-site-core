"Build the open-source game repo and the play site from the 119 legacy games."
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

OLD = S.PROJECT / "poyi-site"
GAMES = S.PROJECT / "cryptography-games"
PLAY = S.PROJECT / "cryptography-site-play"
SHARED = S.CORE / "shared"
ASSET_SCRIPTS = S.CORE / "scripts" / "assets"

CATEGORY_ORDER = ["古典与手工", "机械与战争", "编码与谜题", "现代密码", "协议与信任", "安全与实验", "量子与后量子"]

COLORS = {
    "古典与手工": "orange",
    "机械与战争": "purple",
    "编码与谜题": "blue",
    "现代密码": "mint",
    "协议与信任": "pink",
    "安全与实验": "yellow",
    "量子与后量子": "blue",
}

MECH = {"enigma", "bombe", "purple", "m209", "lorenz", "typex", "plugboard", "stepping-switch", "jefferson-disk", "alberti-disc", "caesrwheel", "maker", "campaign", "jn25", "venona", "adfgvx", "adfgx", "adfgvx2", "hill", "trifid", "bifid", "foursquare", "twosquare", "phillips", "chaocipher", "lindstrom"}
ENC = {"morse", "morselong", "morsetap", "binary", "base64", "braille", "tapcode", "semaphore", "pigpen", "a1z26", "rot47", "fracmorse", "pollux", "monome-dinome", "tridigital", "syllabary", "nullcipher", "acrostic", "book-cipher", "fanqie", "navajo-talker"}
MODERN = {"rsa", "shamir", "sm4", "aes-lab", "block-modes", "hashlab", "totp-verify", "homomorphic-lab", "gm-gateway"}
PROTO = {"pgp-mail", "tor-onion", "dh-handshake", "millionaire", "blind-sign", "zkp-cave", "shamir"}
SECURITY = {"phishhunt", "password-vault", "side-channel-lab", "intel-assess", "homomorphic-lab"}
QUANTUM = {"bb84", "qkd-sim", "pqc-match"}

COURSE = {
    "古典与手工": "d02-monoalphabetic",
    "机械与战争": "d05-rotor-mechanical",
    "编码与谜题": "d01-foundations",
    "现代密码": "d08-block-ciphers",
    "协议与信任": "d14-protocols-pki",
    "安全与实验": "d23-applied-security",
    "量子与后量子": "d22-post-quantum",
}
COURSE_OVERRIDE = {
    "rsa": "d11-asymmetric", "sm4": "d20-china-sm", "gm-gateway": "d20-china-sm",
    "bb84": "d21-quantum-crypto", "qkd-sim": "d21-quantum-crypto", "pqc-match": "d22-post-quantum",
    "shamir": "d16-secret-sharing-mpc", "zkp-cave": "d15-zkp", "block-modes": "d08-block-ciphers",
    "hashlab": "d09-hashes", "totp-verify": "d10-auth-aead", "pgp-mail": "d14-protocols-pki",
    "dh-handshake": "d11-asymmetric", "side-channel-lab": "d17-side-channel", "homomorphic-lab": "d16-secret-sharing-mpc",
}


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


def category(gid):
    if gid in QUANTUM: return "量子与后量子"
    if gid in SECURITY: return "安全与实验"
    if gid in PROTO: return "协议与信任"
    if gid in MODERN: return "现代密码"
    if gid in ENC: return "编码与谜题"
    if gid in MECH: return "机械与战争"
    return "古典与手工"


def build_knowledge_map(entries):
    by_norm = {}
    for e in entries:
        by_norm.setdefault(norm(e["id"]), []).append(e)
        for a in (e.get("aliases") or []):
            by_norm.setdefault(norm(a), []).append(e)
        if e.get("title_en"):
            by_norm.setdefault(norm(e["title_en"]), []).append(e)
    # Manual anchors for games whose slugs collide with people / generic words.
    manual = {
        "caesar": "caesar-cipher", "enigma": "machine--enigma", "morse": "morse-code",
        "vigenere": "vigen-re", "substitution": "substitution",
        "codebreak": "attack--frequency-analysis", "codeguess": "attack--dictionary-attack",
        "morselong": "morse-code", "detective": "attack--frequency-analysis", "freq": "attack--frequency-analysis",
        "bifid": "bifid-cipher", "bombe": "machine--bombe", "trifid": "trifid-cipher",
        "acrostic": "cn-cangtou", "homophonic": "homophonic-substitution", "nomenclator": "nomenclator",
        "nullcipher": "null-cipher", "chaocipher": "chaocipher", "purple": "machine--purple", "m209": "m209",
        "playfair": "term--playfair", "atbash": "atbash", "polybius": "polybius-square",
        "bacon": "bacon-s-biliteral", "railfence": "rail-fence", "affine": "affine-cipher",
        "hill": "hill-cipher", "adfgvx": "adfgvx",
        "nihilist": "nihilist-cipher", "autokey": "autokey-cipher", "solitaire": "solitaire-cipher",
        "alberti-disc": "alberti-cipher-disk", "cardan-grille": "cardan-grille", "jefferson-disk": "jefferson-disk",
        "lorenz": "lorenz-cipher", "typex": "typex",
        "bb84": "bb84", "rsa": "algorithm--rsa", "sm4": "algorithm--sm4", "aes-lab": "algorithm--aes",
        "block-modes": "block-cipher-mode", "hashlab": "cryptographic-hash", "totp-verify": "totp",
        "pgp-mail": "pgp", "tor-onion": "tor", "dh-handshake": "diffie-hellman-key-exchange",
        "gm-gateway": "sm2", "millionaire": "oblivious-transfer", "blind-sign": "algorithm--blind-signature",
        "zkp-cave": "zero-knowledge-proof", "shamir": "shamir-secret-sharing",
        "side-channel-lab": "attack--side-channel-attack", "homomorphic-lab": "homomorphic-encryption",
        "qkd-sim": "bb84", "pqc-match": "algorithm--kyber", "phishhunt": "attack--phishing",
        "password-vault": "password-manager", "intel-assess": "attack--known-plaintext-attack",
        "blockchain-miner": "hashcash", "base64": "base64", "braille": "braille",
        "tapcode": "tap-code", "semaphore": "semaphore", "pigpen": "pigpen-cipher",
        "a1z26": "a1z26", "rot47": "rot47", "morse": "morse-code", "binary": "binary-code",
        "xor": "xor", "venona": "venona", "jn25": "jn-25", "plugboard": "plugboard",
        "bombe": "machine--bombe", "stepping-switch": "stepping-switch", "maker": "cipher-machine",
        "workshop": "cryptanalysis", "campaign": "attack--known-plaintext-attack",
    }
    by_id = {e["id"]: e for e in entries}
    out = {}
    for gid in [g["id"] for g in json.loads((S.PROJECT / "preview-new-site" / "games.json").read_text(encoding="utf-8"))]:
        hit = None
        if gid in manual and manual[gid] in by_id:
            hit = by_id[manual[gid]]
        if not hit:
            n = norm(gid)
            candidates = by_norm.get(n, [])
            if len(candidates) == 1:
                hit = candidates[0]
            else:
                # exact id / title beats prefix contains
                hit = next((e for e in entries if norm(e["id"]) == n), None)
        out[gid] = [hit["id"]] if hit else []
    return out


def manifest(entries):
    games = json.loads((S.PROJECT / "preview-new-site" / "games.json").read_text(encoding="utf-8"))
    kmap = build_knowledge_map(entries)
    rows = []
    for g in games:
        cat = category(g["id"])
        rows.append({
            "id": g["id"],
            "title": g["title"],
            "desc": g["desc"],
            "icon": g["icon"],
            "path": f'games/{g["id"]}/index.html',
            "mobile": g.get("mobile", "ok"),
            "bestMode": g.get("bestMode"),
            "level": g.get("lvl", "mid"),
            "time": g.get("time", ""),
            "category": cat,
            "color": COLORS[cat],
            "knowledgeIds": kmap.get(g["id"], []),
            "courseId": COURSE_OVERRIDE.get(g["id"], COURSE[cat]),
        })
    return {"version": 1, "count": len(rows), "games": rows}


def copy_game_assets():
    preserved = {}
    for name in ("LICENSE-AUDIT.md", "ATTRIBUTION.md"):
        p = GAMES / name
        if p.exists():
            preserved[name] = p.read_text(encoding="utf-8")
    github_dir = None
    if (GAMES / ".github").is_dir():
        github_dir = Path(tempfile.mkdtemp(prefix="games-github-"))
        shutil.copytree(GAMES / ".github", github_dir / ".github")
    if GAMES.exists():
        shutil.rmtree(GAMES)
    GAMES.mkdir(parents=True)
    shutil.copytree(OLD / "games", GAMES / "games")
    shutil.copytree(OLD / "assets", GAMES / "assets")
    for name in ("main.css", "play.css", "logo.svg", "icon-192.png", "icon-512.png"):
        shutil.copy2(SHARED / name, GAMES / "assets" / name)
    for name in ("local-links.js", "play.js"):
        shutil.copy2(ASSET_SCRIPTS / name, GAMES / "assets" / name)
    for name, text in preserved.items():
        (GAMES / name).write_text(text, encoding="utf-8")
    if github_dir:
        shutil.copytree(github_dir / ".github", GAMES / ".github")
    # License, with the repo name updated.
    lic = (OLD / "LICENSE").read_text(encoding="utf-8")
    lic = lic.replace("poyinet/www", "poyinet/cryptography-games")
    (GAMES / "LICENSE").write_text(lic, encoding="utf-8")


def patch_game_pages(root: Path, canonical_base: str = ""):
    count = 0
    for p in (root / "games").glob("*/index.html"):
        text = p.read_text(encoding="utf-8")
        text = text.replace("/manifest.webmanifest", "../../manifest.webmanifest")
        text = text.replace("/assets/icons/apple-touch-icon.png", "../../assets/icons/apple-touch-icon.png")
        text = text.replace('<script src="../../assets/js/pwa.js"></script>', "")
        text = text.replace('<script src="/assets/js/pwa.js"></script>', "")
        # Root-absolute references outside the two known ones would break GitHub project pages.
        text = text.replace('href="/assets/', 'href="../../assets/')
        text = text.replace('src="/assets/', 'src="../../assets/')
        if canonical_base:
            text = text.replace("https://poyi.net/games/", canonical_base)
        p.write_text(text, encoding="utf-8")
        count += 1
    return count


def make_manifest(root: Path):
    payload = {
        "name": "密码学探索馆 · 游戏厅",
        "short_name": "密码游戏",
        "description": "119 款密码学游戏：从凯撒、恩尼格玛到 BB84、后量子迁移，打开即玩。",
        "lang": "zh-CN",
        "dir": "ltr",
        "id": "./",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#faf9f5",
        "theme_color": "#faf9f5",
        "icons": [
            {"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    (root / "manifest.webmanifest").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def card_html(g, prefix: str, learn_prefix: str, main_prefix: str):
    kids = g.get("knowledgeIds") or []
    know = ""
    if kids:
        know = f'<span class="game-know">知识：{html.escape(kids[0])}</span>'
    else:
        know = '<span class="game-know empty">对应课程：' + html.escape(g.get("courseId", "")) + "</span>"
    return f'''<a class="game-card {g.get("color", "orange")}" data-game-card data-category="{html.escape(g["category"])}" data-level="{html.escape(g["level"])}" data-search="{html.escape(g["id"] + " " + g["title"] + " " + g["desc"] + " " + g["category"])}" href="{prefix}{g["id"]}/" data-game-link="{html.escape(g["id"])}"><div class="game-art"><span class="game-badge">{html.escape(g["category"])}</span><span class="game-icon" aria-hidden="true">{g["icon"]}</span><span class="game-play" aria-hidden="true">▶</span></div><div class="game-card-copy"><h3>{html.escape(g["title"])}</h3><p>{html.escape(g["desc"])}</p><div class="game-meta"><span>{html.escape(g["level"])}</span><span>{html.escape(g.get("time", ""))}</span><span>{html.escape(g.get("mobile", ""))}</span></div>{know}</div><span class="game-card-link" aria-hidden="true"></span></a>'''


def lobby(games, mode: str, learn_prefix: str, main_prefix: str):
    cats = [c for c in CATEGORY_ORDER if any(g["category"] == c for g in games)]
    cat_buttons = '<button type="button" data-filter-cat="" aria-pressed="true">全部</button>' + "".join(
        f'<button type="button" data-filter-cat="{html.escape(c)}" aria-pressed="false">{html.escape(c)}</button>' for c in cats
    )
    lvl_buttons = "".join(
        f'<button type="button" data-filter-level="{v}" aria-pressed="false">{label}</button>'
        for v, label in [("easy", "入门"), ("mid", "进阶"), ("hard", "挑战")]
    )
    cards = "".join(card_html(g, ("games/" if mode == "demo" else "/game/"), learn_prefix, main_prefix) for g in games)
    intro = (
        "119 款游戏全部来自开源仓，点开即玩；GitHub 上也能直接跑，不需要先进主站。"
        if mode == "demo" else
        "119 款游戏，从手工破译到后量子迁移。每一款都能回到一条知识条目或一门课。"
    )
    title = "开源游戏仓 · 直接试玩" if mode == "demo" else "游戏厅"
    body = f'''<section class="play-hero"><div><p class="hero-eyebrow">PLAY · {"OPEN SOURCE DEMO" if mode == "demo" else "游戏站"}</p><h1>{title}<br><em>打开就能玩</em></h1><p>{intro}</p><div class="hero-actions"><a class="button primary" href="#games">挑一款开始 <span aria-hidden="true">↓</span></a><a class="quiet-link" href="{main_prefix}">回主站知识库 <span aria-hidden="true">↗</span></a></div></div><div><div class="play-stat-grid"><div class="play-stat"><strong>119</strong><span>可玩游戏</span></div><div class="play-stat"><strong>7</strong><span>玩法分类</span></div><div class="play-stat"><strong>0</strong><span>账号要求</span></div><div class="play-stat"><strong>MIT</strong><span>游戏代码许可</span></div></div><p class="learn-note">游戏只记本机成绩；不登录、不埋点、不依赖私有 API。</p></div></section>
<section class="section" id="games"><div class="play-toolbar"><input type="search" data-game-search placeholder="搜游戏、主题或关键词…" aria-label="搜索游戏"><span class="play-count" data-game-count>119 / 119 款</span></div><div class="play-toolbar" style="margin-top:0"><span style="font-size:11px;color:var(--muted)">分类</span>{cat_buttons}<span style="font-size:11px;color:var(--muted);margin-left:8px">难度</span>{lvl_buttons}</div><div class="game-grid" data-game-grid>{cards}</div><div class="game-empty" data-game-empty hidden>没有匹配的游戏，换个关键词试试。</div><p class="play-footnote">{("这是 GitHub Pages 直玩版：游戏页在 <code>games/&lt;slug&gt;/</code>，链接全部相对路径。" if mode == "demo" else "正式游戏站在 play.poyi.net；开源试玩地址在 poyinet.github.io/cryptography-games，两处使用同一份游戏源。")}</p></section>'''
    return body


def demo_page(games):
    cards_nav = f'''<header class="site-header"><div class="header-inner"><a class="brand" href="./"><img class="logo-mark" src="assets/logo.svg" alt="" width="40" height="40"><span class="brand-words"><strong>密码学探索馆</strong><small>OPEN SOURCE ARCADE</small></span></a><nav class="desktop-nav"><a href="{S.MAIN}/">知识</a><a href="{S.LEARN}/">学习</a><a href="{S.PLAY}/">正式游戏站</a><a href="{S.GITHUB_GAMES}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></nav><div class="header-actions"><button class="icon-button theme-button" type="button" data-theme-toggle aria-label="切换明暗主题"><span data-theme-icon>☀</span></button></div></div></header>'''
    body = lobby(games, "demo", S.LEARN, S.MAIN)
    # Demo header replaces the absolute-assets shell from site_common.
    return f'''<!doctype html><html lang="zh-CN" data-site="demo"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#faf9f5"><meta name="description" content="119 款密码学游戏开源直玩：凯撒、恩尼格玛、AES、RSA、BB84、后量子迁移。"><title>开源游戏仓 · 密码学探索馆</title><link rel="icon" href="assets/logo.svg"><link rel="stylesheet" href="assets/main.css"><link rel="stylesheet" href="assets/play.css"></head><body class="game-demo-lobby">{cards_nav}<main id="main">{body}</main><footer class="site-footer"><div class="footer-inner"><a class="brand" href="./"><img class="logo-mark" src="assets/logo.svg" alt=""><span><strong>密码学探索馆</strong><small>开源游戏仓 · MIT / CC BY 4.0</small></span></a><div class="footer-links"><a href="{S.GITHUB_GAMES}" target="_blank" rel="noopener noreferrer">GitHub 仓库 ↗</a><a href="{S.MAIN}/">主站</a><a href="{S.PLAY}/">正式游戏站</a></div></div><p class="footer-note">游戏代码 MIT；文本与设计 CC BY 4.0；第三方素材保留各自声明。<span aria-hidden="true">✦</span></p></footer><script src="assets/local-links.js"></script><script src="assets/play.js"></script></body></html>'''


def write_page(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build_play_site(games):
    github_dir = None
    if (PLAY / ".github").is_dir():
        github_dir = Path(tempfile.mkdtemp(prefix="play-github-"))
        shutil.copytree(PLAY / ".github", github_dir / ".github")
    if PLAY.exists():
        shutil.rmtree(PLAY)
    PLAY.mkdir(parents=True)
    if github_dir:
        shutil.copytree(github_dir / ".github", PLAY / ".github")
    patch_game_pages(PLAY, "https://play.poyi.net/games/")
    shutil.copytree(GAMES / "games", PLAY / "games")
    shutil.copytree(GAMES / "assets", PLAY / "assets")
    for name in ("main.css", "play.css", "logo.svg", "icon-192.png", "icon-512.png", "local-links.js", "play.js"):
        src = GAMES / "assets" / name
        if src.exists():
            shutil.copy2(src, PLAY / "assets" / name)
    shutil.copy2(GAMES / "manifest.webmanifest", PLAY / "manifest.webmanifest")
    shutil.copy2(GAMES / "games-manifest.json", PLAY / "games-manifest.json")
    write_page(PLAY, "index.html", S.page(site="play", lang="zh", title="游戏厅", description="119 款密码学游戏：从凯撒到后量子。", body=lobby(games, "play", S.LEARN, S.MAIN), path="/", active="play", extra_css="play.css"))
    for g in games:
        gid = g["id"]
        path = f'/game/{gid}/'
        body = f'''<div class="breadcrumbs"><a href="/">游戏厅</a><span>/</span><span>{html.escape(g["title"])}</span></div><section class="player-page"><div class="player-top"><h1>{html.escape(g["title"])}</h1><div class="player-badges"><span>{html.escape(g["category"])}</span><span>{html.escape(g["level"])}</span><span>{html.escape(g.get("time", ""))}</span><span>{html.escape(g.get("mobile", ""))}</span></div></div><div class="player-frame"><iframe src="../../games/{gid}/index.html" title="{html.escape(g["title"])}" loading="eager" allow="fullscreen"></iframe><div class="player-frame-bar"><a href="/">← 回大厅</a><button type="button" data-fullscreen>全屏</button></div></div><div class="player-info"><div><h2>这一关在练什么</h2><p>{html.escape(g["desc"])}</p><div class="player-actions"><a class="button primary" href="/">换一款</a><a class="button secondary" href="{S.LEARN}/courses/{g["courseId"]}/">对应课程 ↗</a>{f'<a class="quiet-link" href="{S.MAIN}/entries/{g["knowledgeIds"][0]}/">相关知识 ↗</a>' if g.get("knowledgeIds") else ''}</div></div><aside class="player-side"><h3>游戏信息</h3><ul><li>难度：{html.escape(g["level"])}</li><li>设备：{html.escape(g.get("mobile", ""))} / 触屏友好</li><li>时长：{html.escape(g.get("time", ""))}</li><li>计分：{html.escape(str(g.get("bestMode") or "不记分"))}</li></ul><a class="side-link" href="{S.GITHUB_GAMES}" target="_blank" rel="noopener noreferrer"><span>开源游戏源</span><span>↗</span></a><a class="side-link" href="{S.PLAY}/"><span>回游戏厅</span><span>←</span></a></aside></div></section>'''
        write_page(PLAY, f"game/{gid}/index.html", S.page(site="play", lang="zh", title=g["title"], description=g["desc"], body=body, path=path, active="play", noindex=True, extra_css="play.css"))
    write_page(PLAY, "sitemap.xml", S.sitemap(S.PLAY, ["/"] + [f'/game/{g["id"]}/' for g in games]))
    write_page(PLAY, "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {S.PLAY}/sitemap.xml\n")
    write_page(PLAY, "CNAME", "play.poyi.net\n")
    write_page(PLAY, ".nojekyll", "")
    write_page(PLAY, "404.html", S.page(site="play", lang="zh", title="没有这款游戏", description="游戏站 404", body='<div class="page-heading"><p class="eyebrow">404</p><h1>这一关不在游戏厅</h1><p>回到大厅，按分类或难度重新选一款。</p></div><div class="hero-actions"><a class="button primary" href="/">回游戏厅</a></div>', path="/404.html", active="play", noindex=True, extra_css="play.css"))


def main():
    _, entries = S.load_catalog()
    games_payload = manifest(entries)
    copy_game_assets()
    patched = patch_game_pages(GAMES, "https://poyinet.github.io/cryptography-games/games/")
    make_manifest(GAMES)
    (GAMES / "games-manifest.json").write_text(json.dumps(games_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_page(GAMES, "index.html", demo_page(games_payload["games"]))
    write_page(GAMES, ".nojekyll", "")
    write_page(GAMES, "README.md", f'''# cryptography-games

密码学探索馆的开源游戏仓：**119 款可直玩游戏**，从凯撒、恩尼格玛到 AES、RSA、BB84 与后量子迁移。

## 直接试玩

GitHub Pages：<{S.GAME_DEMO}/>

每款游戏位于 `games/<slug>/index.html`，全部使用相对路径，可直接在 GitHub Pages 项目页运行。

## 许可

- 游戏代码：MIT（见 `LICENSE`）
- 文本与界面设计：CC BY 4.0
- 第三方图片、音频、字体保留各自声明；发布前逐项复核。

## 与三站的关系

- 正式游戏站：<{S.PLAY}/>（由 `cryptography-site-play` 发布）
- 知识主站：<{S.MAIN}/>
- 学习站：<{S.LEARN}/>

`games-manifest.json` 是游戏元数据与知识映射的唯一清单；正式站和 GitHub 直玩版都从同一份游戏源构建。
''')
    build_play_site(games_payload["games"])
    print(json.dumps({"games": games_payload["count"], "patched": patched, "play_pages": len(list(PLAY.rglob('*.html')))} , ensure_ascii=False))


if __name__ == "__main__":
    main()
