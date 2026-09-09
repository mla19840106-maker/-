# Prompts — 资深党政机关办文参谋 提示词库

本目录收录 **资深党政机关办文参谋 3.4 完整版** 全量提示词，便于在 GitHub 上长期保存、版本管理与随时调取审核。

## 目录结构

```
prompts/
├── 资深党政机关办文参谋-3.4完整版.md  # ★ 完整版（29章全量，可作系统提示词/纸质核查表）
├── 精简版-快速调用.md                  # 精简版一键复制区（短对话/移动端）
├── prompt.json                         # 结构化元数据+精简prompt（便于API调用）
└── README.md                           # 本说明
```

## 快速调取

### 方式1：GitHub 网页直接复制
打开 `资深党政机关办文参谋-3.4完整版.md` → 右上角 `Raw` → 全选复制 → 粘贴到 AI 的系统提示词。

### 方式2：精简版（推荐日常）
打开 `精简版-快速调用.md` → 复制"一键复制区"代码块 → 粘贴即用。

### 方式3：命令行 / API 拉取
```bash
# 拉取完整版
curl -s https://raw.githubusercontent.com/mla19840106-maker/-/main/prompts/资深党政机关办文参谋-3.4完整版.md

# 拉取精简版 prompt（JSON）
curl -s https://raw.githubusercontent.com/mla19840106-maker/-/main/prompts/prompt.json | jq -r .prompt_compact

# 拉取精简版 markdown
curl -s https://raw.githubusercontent.com/mla19840106-maker/-/main/prompts/精简版-快速调用.md
```

### 方式4：git clone
```bash
git clone https://github.com/mla19840106-maker/-.git
cat prompts/精简版-快速调用.md
```

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.4 完整版 | 2026-09-09 | 含国企专版·事业单位与基层专版·全维度词汇限制·规范提法豁免·口径矩阵·建设性写法·数字标点细则·多轮留痕（29章） |

## 使用建议

- **A类材料**（整改/检讨/巡视整改/请示人财物/对外发布）务必用完整版全量审查
- **B类材料**（汇报/总结/方案/讲话）可用精简版+重点扫描
- **C类材料**（润色/提纲/内部通知）精简版快速通过即可

## 维护

- 后续修订请在 `prompts/` 下新增版本文件，保留历史版本便于追溯
- 建议每次修订更新 `prompt.json` 中的 `version` 和 `created`
- 重大修订同步更新根目录 `README.md` 的版本说明
