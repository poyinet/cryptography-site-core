"Shared site data and HTML shell for the three-site build."
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml

CORE = Path(__file__).resolve().parents[1]
PROJECT = CORE.parent
CONFIG = json.loads((CORE / "config" / "sites.json").read_text(encoding="utf-8"))
CONTENT = PROJECT / "cryptography-decode-history"
SITES = CONFIG["sites"]
MAIN = SITES["main"]["origin"]
LEARN = SITES["learn"]["origin"]
PLAY = SITES["play"]["origin"]
GAME_DEMO = CONFIG["gameDemo"]["origin"]
GITHUB_CONTENT = "https://github.com/poyinet/cryptography-decode-history"
GITHUB_GAMES = "https://github.com/poyinet/cryptography-games"

SITE_NAME = "密码学探索馆"
SITE_EN = "CRYPTOGRAPHY ATLAS"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def plain(value) -> str:
    text = re.sub(r"[*_`#>|]+", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def excerpt(value, limit=280) -> str:
    text = plain(value)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("。", "；", ". ", "！", "？"):
        pos = cut.rfind(sep)
        if pos > limit * 0.55:
            cut = cut[: pos + 1]
            break
    return cut + "…"


def load_catalog():
    data = json.loads((CONTENT / "_meta" / "catalog" / "catalog.json").read_text(encoding="utf-8"))
    entries = [e for e in data.get("entries", []) if e.get("status") != "excluded"]
    return data, entries


def load_domains():
    doc = yaml.safe_load((CONTENT / "_meta" / "inventory" / "domains.yaml").read_text(encoding="utf-8"))
    return {d["id"]: d for d in doc.get("entries", []) if d.get("type") == "domain"}


def load_articles():
    articles = []
    for p in sorted((CONTENT / "_meta" / "reviewed").glob("*/content.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for a in doc.get("entries", []):
            if isinstance(a, dict) and a.get("id"):
                a["_batch"] = p.parent.name
                articles.append(a)
    return articles


def article_index(articles):
    by_entry = defaultdict(list)
    by_id = {}
    for a in articles:
        by_id[a["id"]] = a
        ids = a.get("inventoryIds") or []
        if isinstance(ids, str):
            ids = [ids]
        for eid in ids:
            by_entry[eid].append(a)
    best = {}
    for eid, rows in by_entry.items():
        rows.sort(key=lambda a: (a.get("coverage") != "catalog-entry", len(a.get("inventoryIds") or []), a["id"]))
        best[eid] = rows[0]
    return best, by_id


def article_text(a, lang, key):
    if not a:
        return ""
    sections = a.get("sections") or {}
    return (sections.get(lang) or {}).get(key) or ""


def entry_primary_domain(e):
    doms = e.get("domain") or []
    return doms[0] if doms else "d01-foundations"


TRACKS = [
    {
        "id": "foundations",
        "title": "基础与古典",
        "en": "Foundations & Classical",
        "desc": "从术语、字母表与手工替换出发，先学会把明文、密文、算法和密钥分开看。",
        "domains": ["d01-foundations", "d02-monoalphabetic", "d03-polyalphabetic", "d04-transposition", "d07-cryptanalysis"],
        "color": "purple",
    },
    {
        "id": "machines",
        "title": "机器、密钥与流",
        "en": "Machines, Keys & Streams",
        "desc": "转轮、电报、一次性密码本与密钥管理：当手工规则变成机器和流程，安全性从哪里来。",
        "domains": ["d05-rotor-mechanical", "d06-otp-stream", "d13-key-management", "d19-randomness"],
        "color": "blue",
    },
    {
        "id": "modern",
        "title": "现代密码",
        "en": "Modern Cryptography",
        "desc": "分组、哈希、认证、公钥、签名、协议与零知识：现代密码学的主干与相互依赖。",
        "domains": ["d08-block-ciphers", "d09-hashes", "d10-auth-aead", "d11-asymmetric", "d12-signatures", "d14-protocols-pki", "d15-zkp", "d16-secret-sharing-mpc"],
        "color": "mint",
    },
    {
        "id": "security",
        "title": "应用、历史与理论",
        "en": "Applications, History & Theory",
        "desc": "把密码放进真实系统：侧信道、隐写、国密、工程安全与可证明的理论边界。",
        "domains": ["d17-side-channel", "d18-steganography", "d20-china-sm", "d23-applied-security", "d24-theory"],
        "color": "orange",
    },
    {
        "id": "quantum",
        "title": "量子与后量子",
        "en": "Quantum & Post-Quantum",
        "desc": "量子密钥分发、量子威胁与后量子迁移：下一代密码学要回答的问题。",
        "domains": ["d21-quantum-crypto", "d22-post-quantum"],
        "color": "pink",
    },
]

DOMAIN_DESC = {
    "d01-foundations": "术语、威胁模型与密码学的基本问题：先建立一套能反复使用的语言。",
    "d02-monoalphabetic": "单表替换家族：凯撒、仿射、同音替换，以及它们为什么挡不住频率分析。",
    "d03-polyalphabetic": "多表替换：维吉尼亚、博福特、波特等，用周期密钥对抗字母频率。",
    "d04-transposition": "换位与栅栏：不换字母，只改顺序；排列空间和已知明文如何暴露结构。",
    "d05-rotor-mechanical": "转轮与机械密码机：恩尼格玛、紫密、M-209、洛伦兹与 Typex。",
    "d06-otp-stream": "一次性密码本与流密码：密钥流、重用、异或与同步问题。",
    "d07-cryptanalysis": "破译方法：频率、重合指数、卡斯基基、差分、线性与中间相遇。",
    "d08-block-ciphers": "分组密码：DES、AES、SM4 与工作模式，理解扩散、混淆和模式选择。",
    "d09-hashes": "哈希与消息摘要：单向性、抗碰撞、雪崩效应与口令派生。",
    "d10-auth-aead": "消息认证与 AEAD：MAC、GCM、Poly1305 与“先加密还是先认证”。",
    "d11-asymmetric": "公钥密码：RSA、ElGamal、椭圆曲线与格基方案的陷门从哪来。",
    "d12-signatures": "数字签名：签名、验签、盲签、环签名与门限签名的信任边界。",
    "d13-key-management": "密钥管理：生成、分发、轮换、撤销与托管，往往比算法更难。",
    "d14-protocols-pki": "协议与 PKI：TLS、证书、ACME、Kerberos 与中间人攻击的防线。",
    "d15-zkp": "零知识证明：完备性、可靠性与零知识三性，以及 Fiat-Shamir 启发式。",
    "d16-secret-sharing-mpc": "秘密共享与 MPC：Shamir 门限、混淆电路与多方计算的信任假设。",
    "d17-side-channel": "侧信道与物理攻击：时间、功耗、缓存、故障注入与声学泄露。",
    "d18-steganography": "隐写与信息隐藏：把消息藏进载体，和“加密”不是同一件事。",
    "d19-randomness": "随机数与 CSPRNG：种子、熵源、伪随机与可预测性。",
    "d20-china-sm": "中国国密：SM2、SM3、SM4、SM9 与标准体系的阅读入口。",
    "d21-quantum-crypto": "量子密码：BB84、量子密钥分发、量子威胁与量子资源。",
    "d22-post-quantum": "后量子密码：Kyber、Falcon、McEliece 与迁移路线。",
    "d23-applied-security": "应用安全工程：口令、钓鱼、存储、TEE、供应链与真实系统。",
    "d24-theory": "理论基础：计算困难性、归约、可证明安全与密码学模型。",
}


def build_courses(entries, domains):
    primary = defaultdict(list)
    for e in entries:
        primary[entry_primary_domain(e)].append(e)
    courses = []
    for track in TRACKS:
        for did in track["domains"]:
            d = domains.get(did)
            if not d:
                continue
            rows = sorted(primary.get(did, []), key=lambda e: (int(e.get("level") or 9), e.get("title") or ""))
            courses.append({
                "id": did,
                "code": did.split("-")[0],
                "title": d.get("title") or did,
                "title_en": d.get("title_en") or d.get("title") or did,
                "desc": DOMAIN_DESC.get(did, d.get("note") or ""),
                "track": track["id"],
                "track_title": track["title"],
                "color": track["color"],
                "entries": rows,
                "count": len(rows),
            })
    return courses


def course_for_entry(courses, eid):
    for c in courses:
        if any(e["id"] == eid for e in c["entries"]):
            return c
    return courses[0]


def _nav_items():
    return [
        ("knowledge", "知识", "Knowledge", MAIN + "/"),
        ("learn", "学习", "Learn", LEARN + "/"),
        ("play", "游戏", "Play", PLAY + "/"),
        ("search", "搜索", "Search", MAIN + "/search/"),
        ("about", "关于", "About", MAIN + "/about/"),
    ]


def nav(active: str = "", lang: str = "zh", alt_href: str | None = None) -> str:
    links = []
    for key, label, label_en, url in _nav_items():
        current = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{url}"{current}>{label if lang == "zh" else label_en}</a>')
    language = ""
    if alt_href:
        language = f'<a class="language-button" href="{esc(alt_href)}" aria-label="切换语言">🌐 <span>{"EN" if lang == "zh" else "中文"}</span></a>'
    return f'''<header class="site-header"><div class="header-inner">
<a class="brand" href="{MAIN}/"><img class="logo-mark" src="/assets/logo.svg" alt="" width="40" height="40"><span class="brand-words"><strong>{SITE_NAME}</strong><small>{SITE_EN}</small></span></a>
<nav class="desktop-nav" aria-label="主导航">{"".join(links)}</nav>
<div class="header-actions">{language}<button class="icon-button theme-button" type="button" data-theme-toggle aria-label="切换明暗主题"><span data-theme-icon>☀</span></button></div>
</div></header>'''


def bottom_nav(active: str = "", lang: str = "zh") -> str:
    icons = {"knowledge": "◈", "learn": "▤", "play": "▶", "search": "⌕"}
    links = []
    for key, label, label_en, url in _nav_items()[:4]:
        current = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{url}"{current}><span aria-hidden="true">{icons[key]}</span><span>{label if lang == "zh" else label_en}</span></a>')
    return '<nav class="bottom-nav" aria-label="移动导航">' + "".join(links) + "</nav>"


def footer(lang: str = "zh") -> str:
    return f'''<footer class="site-footer"><div class="footer-inner">
<a class="brand" href="{MAIN}/"><img class="logo-mark" src="/assets/logo.svg" alt="" width="40" height="40"><span><strong>{SITE_NAME}</strong><small>知识是正文 · 学习是路线 · 游戏是练习</small></span></a>
<div class="footer-links"><a href="{MAIN}/">主站</a><a href="{LEARN}/">学习站</a><a href="{PLAY}/">游戏站</a><a href="{GITHUB_CONTENT}" target="_blank" rel="noopener noreferrer">内容仓 ↗</a><a href="{GITHUB_GAMES}" target="_blank" rel="noopener noreferrer">游戏仓 ↗</a><span>内容 CC BY 4.0 · 代码 MIT</span></div>
</div><p class="footer-note">一个站，三种走法：在知识里查清楚，在课程里走一遍，在游戏里练一次。<span aria-hidden="true">✦</span></p></footer>'''


def page(
    *,
    site: str,
    lang: str,
    title: str,
    description: str,
    body: str,
    path: str,
    active: str = "",
    alt_href: str | None = None,
    noindex: bool = False,
    body_class: str = "",
    extra_css: str = "",
) -> str:
    origin = SITES[site]["origin"]
    canonical = origin + path
    robots = "noindex,follow" if noindex else "index, follow, max-image-preview:large"
    alt = ""
    if alt_href:
        alt = f'<link rel="alternate" hreflang="{"en" if lang == "zh" else "zh-Hans"}" href="{esc(alt_href)}">'
    return f'''<!doctype html><html lang="{"zh-CN" if lang == "zh" else "en"}" data-site="{site}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="{robots}"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#faf9f5"><meta name="description" content="{esc(description)}"><title>{esc(title)} · {SITE_NAME}</title><link rel="canonical" href="{esc(canonical)}">{alt}<link rel="icon" type="image/svg+xml" href="/assets/logo.svg"><link rel="apple-touch-icon" href="/assets/icon-192.png"><link rel="stylesheet" href="/assets/main.css"><link rel="stylesheet" href="/assets/{extra_css}"></head><body class="{body_class}"><a class="skip-link" href="#main">跳到正文</a>{nav(active, lang, alt_href)}<main id="main">{body}</main>{footer(lang)}{bottom_nav(active, lang)}<script src="/assets/local-links.js" defer></script><script src="/assets/{'learn.js' if site == 'learn' else 'play.js' if site == 'play' else 'site.js'}" defer></script></body></html>'''


def sitemap(origin: str, paths: Iterable[str]) -> str:
    rows = "".join(f"<url><loc>{esc(origin + p)}</loc></url>" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>'
