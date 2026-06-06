# Agent-Skills

个人 Codex skill 仓库，用来沉淀不同场景下可复用的 agent 工作流、脚本和参考资料。

这个仓库不是单一 skill 项目。每个功能都应作为一个独立 skill 放在仓库根目录下，互相之间保持边界清晰。

## 仓库约定

```text
repo-root/
|-- README.md
|-- .gitignore
|-- skill-a/
|   |-- SKILL.md
|   |-- agents/
|   |-- references/
|   `-- scripts/
`-- skill-b/
    |-- SKILL.md
    `-- assets/
```

每个 skill 目录只放 Codex 使用该能力时真正需要的内容：

- `SKILL.md`：必需，包含 YAML frontmatter 和核心使用说明。
- `agents/openai.yaml`：推荐，提供 UI 展示名、短描述和默认提示词。
- `references/`：可选，存放按需读取的背景资料、流程规范、领域知识。
- `scripts/`：可选，存放可重复执行的确定性脚本。
- `assets/`：可选，存放模板、素材或输出时会用到的静态资源。

不要把课程项目、PDF、OCR 缓存、模型文件、临时输出、评估草稿等放进 skill 目录提交到仓库。

## 当前 Skills

| Skill | 用途 | 典型触发方式 |
| --- | --- | --- |
| `teach-pdf-content` | 把用户指定的 PDF 章节、教材片段、论文、讲义或课程阅读材料转换成按章节管理、有来源依据的 Markdown 学习包，包含掌握标准、笔记、练习、记忆卡和复习计划。 | `使用 $teach-pdf-content，基于 <PDF 路径> 的 <页码/章节> 帮我生成学习包。` |

## 使用方式

在 Codex 中直接触发某个 skill 前，先把对应目录安装到本机 Codex skills 目录。

安装单个 skill：

```powershell
Copy-Item -Recurse `
  ".\teach-pdf-content" `
  "$env:USERPROFILE\.codex\skills\teach-pdf-content" `
  -Force
```

然后在对话里明确引用：

```text
使用 $teach-pdf-content，基于 D:\path\to\book.pdf 的第 18-25 页，生成中文学习包。
```

也可以不安装，直接让 Codex 使用仓库中的路径：

```text
使用 D:\实习\Agent Skill\teach-pdf-content 这个 skill，基于 D:\path\to\book.pdf 的第 18-25 页生成学习包。
```

## 新增 Skill 流程

1. 在仓库根目录新建 skill 文件夹，名称使用小写字母、数字和连字符，例如 `paper-reviewer`。
2. 编写 `SKILL.md`，frontmatter 只保留 `name` 和 `description`。
3. 只在需要时添加 `agents/`、`references/`、`scripts/`、`assets/`。
4. 脚本必须能在本地独立运行；复杂或易错流程优先沉淀成脚本。
5. 生成物、源材料、缓存、模型和本地项目放到 `.gitignore` 覆盖的工作区，不提交。
6. 更新本 README 的「当前 Skills」表。

## 验证

验证单个 skill：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\teach-pdf-content
```

验证所有根级 skill：

```powershell
Get-ChildItem -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" $_.FullName
  }
```

推送前检查：

```powershell
git status --short --untracked-files=all
git diff --check
```
