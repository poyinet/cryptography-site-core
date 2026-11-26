# cryptography-site-core

新站的核心与 UI 仓：三站共享一套设计系统、导航、页脚、主题与构建规则。

## 输出

| 站点 | 发布仓 | 域名 | 本地端口 |
|---|---|---|---|
| 主站 / 知识库 | `cryptography-site-main` | `poyi.net` | 8789 |
| 学习站 | `cryptography-site-learn` | `learn.poyi.net` | 8790 |
| 游戏站 | `cryptography-site-play` | `play.poyi.net` | 8791 |
| GitHub 游戏直玩 | `cryptography-games` | `poyinet.github.io/cryptography-games` | 8791 的 `/games/` 同源 |

## 目录

- `config/sites.json`：域名、发布仓、本地端口、GitHub 项目页 base。
- `shared/`：`main.css`（主站设计系统）、`learn.css`、`play.css`、`three-site.css`、logo、图标。
- `scripts/`：`build_learn.py`、`build_games.py`、`postprocess_main.py`、`site_common.py`。
- `scripts/assets/`：`local-links.js`（本地预览域名改写）、`learn.js`（进度/主题）、`play.js`（筛选/全屏/主题）。

## 本地重建

```powershell
cd C:\Users\chenhua\Desktop\poyi\cryptography-decode-history
node tools/site/knowledge/build.mjs --indexable

cd ..
python cryptography-site-core\scripts\build_games.py
python cryptography-site-core\scripts\postprocess_main.py
python cryptography-site-core\scripts\build_learn.py
```

`build_games.py` 先产出 `cryptography-games` 与 `cryptography-site-play`；`build_learn.py` 读取 `cryptography-games/games-manifest.json` 做“相关知识/相关游戏”互链；主站最后从 `cryptography-decode-history/build/knowledge-site` 复制并做三站化后处理。

## 规则

- 知识条目 canonical 只在主站；学习站只放导读、目标、边界与回链；游戏站只放游戏与知识回链。
- 三站共用 `knowledgeId`、`lessonId`（等于条目 id）、`gameSlug`。
- 学习进度：`localStorage` + `Domain=.poyi.net` cookie；本地 127.0.0.1 只写 localStorage。
- 游戏仓不绑自定义域；正式 `play.poyi.net` 由 `cryptography-site-play` 发布，避免 GitHub 项目页与自定义域互抢。
