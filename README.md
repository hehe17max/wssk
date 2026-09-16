# 外设水库 (Waishui Shuiku)

所有人可访问的**自动化外设数据库网站**。核心特点：**无人值守**——定时自动访问品牌官网与权威测评，确认品牌真实性、自动发现新品、自动分类、多源核验参数，并把结果自动发布到网页供访问者检索、筛选与对比。

## 功能

- **6 大外设类型**：耳机 / 鼠标 / 键盘 / 手柄 / 音响 / 鼠标垫（耳机细分 TWS、头戴、游戏、HiFi、骨传导、监听·麦克风；键盘细分 磁轴 / 机械 / 静电容 / 薄膜）
- **品牌筛选**：228 个品牌（含已核验 / 待核验状态标识），保留用户原始分组（手机生态、传统音频、TWS 新锐、HiFi 耳烧、电竞、美/日/德/英/丹麦/法/荷/韩/瑞士/新加坡/中国台湾/中国香港…）
- **搜索栏**：品牌 + 产品名实时搜索
- **关键词快捷筛选**（chips）：TWS、无线、机械、磁轴、HiFi、电竞、静音、RGB、办公、Mac、8K 等，可多选可取消
- **参数筛选**：类型 → 子类型 → 品牌 → 参数（价格、续航、DPI、配列、连接方式等）
- **产品对比**：最多 **20 款**同时横向对比，差异高亮，可导出 CSV
- **数据可信度分级**：每条产品数据标注 多源核验一致 / 官方来源确认 / 来源冲突待复核 / 种子数据待核验 / 待核验

## 自动化流水线（无人核实）

```
定时触发 (GitHub Actions)
   → ① 新品发现     品牌官网 Sitemap / Shopify / 产品列表页
   → ② 自动分类     6 大类型 × 子类型 关键词规则（名称/描述/标签/参数/URL 线索/多语言）
   → ③ 品牌核验     访问官网首页，标题/站点名匹配品牌名 → 确认真实性
   → ④ 产品核验     官方产品页 + 权威测评站，抽取参数数值比对，≥2 来源一致率≥0.6 → 多源核验
   → ⑤ 页面补全     抓取官方产品页标题/描述，回填信息并重新分类
   → ⑥ 入库发布     合并去重 → 重算统计 → 提交 → GitHub Pages 自动更新
```

- 品牌真实性**绝不预填**：匹配成功才标记「已核验」；失败/不可达如实标记「待人工确认 / 核验失败」。
- 每个阶段独立可跑：`python -m pipeline.run <seed|classify|verify|verify-products|discover|enrich|ingest|full>`
- 全链路：`python -m pipeline.run full --limit-brands 6 --limit 5`

## 目录结构

```
waishui-shuiku/
├── config/              # 品牌注册表(228) + 流水线配置
├── pipeline/            # 自动化流水线（classify/verify/discover/enrich/ingest/run）
├── tools/               # 种子生成 seed_data.py、本地服务器 serve.py
├── scripts/             # 数据质量校验 check_data.py
├── data/                # brands.json / products.json / meta.json / pipeline_report.json
├── css/ js/             # 前端样式与逻辑
├── index.html           # 产品库（搜索/筛选/对比入口）
├── compare.html         # 最多 20 款产品对比（差异高亮 + 导出 CSV）
├── about.html           # 架构与自动化说明
└── .github/workflows/   # sync.yml 定时同步 + deploy-pages.yml 部署
```

## 本地运行

```bash
pip install -r requirements.txt
python -m pipeline.run seed          # 生成种子数据（154 款 + 228 品牌）
python -m pipeline.run full          # 跑完整流水线（联网）
python tools/serve.py 8000           # 本地预览
# 浏览器打开 http://127.0.0.1:8000/index.html
python scripts/check_data.py         # 数据质量校验
```

## 部署为公开网站

1. 推送到 GitHub 公开仓库（main 分支）；
2. 仓库 `Settings → Pages → Source → GitHub Actions`；
3. 推送后 `deploy-pages.yml` 自动构建发布，网址 `https://<用户名>.github.io/<仓库名>/`；
4. `sync.yml` 定时（默认每 6 小时，可改 `cron`）自动跑全链路并提交数据，网页自动刷新。

## 数据来源与口径

- 品牌与产品数据由流水线自动从品牌官网、权威测评站抓取与核验；
- 种子数据为公开资料整理，`data_status=seed`（待核验），等待流水线自动核验升级；
- 参数比对为数值级核对（归一化后比较），不一致的产品标记「来源冲突待复核」；
- 每次同步的流水线报告见 `data/pipeline_report.json`。
