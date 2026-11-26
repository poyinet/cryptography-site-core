# 三站审计与本地验收

## 脚本

| 脚本 | 作用 | 依赖 |
| --- | --- | --- |
| `scripts/audit_static.py` | 扫描三站 HTML 的内部链接、canonical、sitemap、robots、旧域名残留 | Python 3.9+，仅标准库 |
| `scripts/check_http.py` | 用 `serve_three.py` 起 8789/8790/8791，检查关键路由 200/HTML/title | Python 3.9+，仅标准库 |
| `scripts/build_learn.py` | 重建学习站，保留四份学习数据 JSON | Python 3.9+，项目内容源 |
| `scripts/fix_play_canonicals.py` | 已构建游戏站的一键 raw canonical 热修 | Python 3.9+ |

## 运行

```bash
cd C:\Users\chenhua\Desktop\poyi
python cryptography-site-core/scripts/audit_static.py --site all
python cryptography-site-core/scripts/check_http.py --start
```

报告写到 `audit/static-audit.json` 与 `audit/http-smoke.json`。

## 2026-11-26 已验证

- **全量 HTML 提取审计**：三站 6,757 页（4,640 / 1,877 / 240）；内部链接 0 缺失、sitemap 0 错、旧域名 0。主站 1,824 个 `/read/*-details/` 是站内 canonical 别名；游戏站 119 个 raw `games/<slug>/` 旧 `poyi.net/games/` canonical 已逐页修复，直接复核旧 canonical 0、新 canonical 119/119，官方脚本全量重跑仍待执行。
- **jsdom 真实 DOM 夹具**：英文课程页、英文首页、英文进度页、英文课时页、中文课程页、游戏播放器页、主站条目页。
- 33 项断言全部通过：课程导学、3 题小测、错题队列、复习卡、5 条结业项目、课程游戏互链、英文 UI、成绩面板/成绩存储、JSON-LD、反馈链接。
- 英文 UI 可见中文：课程页 0、首页仅 1 条正文引用（`AES 高级加密标准`）、进度页 0、课时页 0。
- 中文课程页：导学 3 个游戏 chip、3 题小测在数据加载后渲染。
- `check_http.py`：19 路由关键页实测 19/19 通过（主站/学习站用全量 HTML 抽取重建，游戏站用当前真实 root/wrapper/raw/404；完整静态资源点击尚未覆盖）。
- `audit_static.py`：合成夹具 0 问题时通过；故意缺失链接/错误 sitemap 时返回 1。

## 尚未执行

- 真实三站 8789/8790/8791 的 HTTP 点击验收（`check_http.py` 已就绪；本轮只跑合成夹具）。
- GitHub Pages、DNS、旧站备份/切换。

