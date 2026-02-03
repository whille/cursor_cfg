---
name: video-download
description: 根据视频链接下载 YouTube、B站、优酷等站点视频。基于 yt-dlp，支持数千站点。用户后续只需给出视频 URL，即可协助下载到本地。Use when the user provides a video URL and wants to download it from YouTube, Bilibili, or other supported sites.
---

# 视频链接下载（YouTube / B站等）

根据你给出的**视频链接**，用 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 下载到本地，支持 **YouTube、B站、优酷、抖音** 等大量站点。

## 使用方式

**你只需要发给我视频链接**，我可以：

1. 用本 Skill 的脚本或直接调用 `yt-dlp` 帮你下载
2. 按你的要求选择：保存目录、只要音频、画质、是否带字幕等

示例对话：

- 「帮我下载 https://www.youtube.com/watch?v=xxx」
- 「把这条 B 站链接的视频下到当前目录：https://www.bilibili.com/video/xxx」
- 「只要音频，格式 mp3：https://…」

## 依赖与安装

### 1. 安装 yt-dlp

```bash
# 推荐：pip 安装（便于更新）
pip install yt-dlp

# 或 各系统包管理器
brew install yt-dlp        # macOS
sudo apt install yt-dlp    # Ubuntu/Debian
```

### 2. 安装 FFmpeg（可选但强烈推荐）

用于合并音视频、转码、提取音频等：

```bash
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu/Debian
```

## 基本用法

### 命令行直接使用 yt-dlp

```bash
# 下载一条链接（默认当前目录、最佳画质）
yt-dlp "https://www.youtube.com/watch?v=xxx"

# 指定保存目录
yt-dlp -o "/path/to/dir/%(title)s.%(ext)s" "https://www.bilibili.com/video/BVxxx"

# 仅下载音频并转为 mp3
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=xxx"

# 下载字幕（若有）
yt-dlp --write-subs --sub-langs zh-Hans,en "https://..."
```

### 使用本 Skill 提供的脚本

```bash
# 下载到当前目录
python scripts/download_video.py "https://www.youtube.com/watch?v=xxx"

# 指定输出目录
python scripts/download_video.py "https://..." -o ./downloads

# 仅音频 mp3
python scripts/download_video.py "https://..." --audio-only
```

## 常用站点与说明

| 站点 | 示例链接 | 说明 |
|------|----------|------|
| YouTube | `youtube.com/watch?v=...` | 需网络可访问；可配 cookies 下会员/年龄限制 |
| B站 | `bilibili.com/video/BV...` | 部分高清晰度/会员需 cookies |
| 优酷 / 爱奇艺 / 腾讯 | 各站播放页链接 | 受站点限制，部分需登录/cookies |
| 抖音 / 推特 / 等 | 各站分享链接 | 以 yt-dlp 支持列表为准 |

**B 站会员 / 高清晰度**：可用 `--cookies-from-browser chrome` 从浏览器带登录状态，或 `--cookies cookies.txt` 指定 cookies 文件。

## 常用参数速查

| 参数 | 含义 |
|------|------|
| `-o TEMPLATE` | 输出路径/文件名模板，如 `%(title)s.%(ext)s` |
| `-P DIR` / `-o "DIR/%(title)s.%(ext)s"` | 保存到指定目录 |
| `-f FORMAT` | 指定清晰度，如 `bestvideo+bestaudio`、`bv*+ba/b` |
| `-x` / `--extract-audio` | 只保留音频 |
| `--audio-format mp3` | 转成 mp3（需 ffmpeg） |
| `--write-subs` / `--sub-langs zh,en` | 下载字幕 |
| `--cookies-from-browser chrome` | 使用 Chrome 的 cookies |
| `-F` | 列出当前视频所有可用格式再选 |

## 参考仓库

- [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) — 主工具，支持站点列表见 [supportedsites.md](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- [soimort/you-get](https://github.com/soimort/you-get) — 国内站点备选方案

## 注意

- 仅下载你有权观看的內容，遵守各站点服务条款与版权法律。
- 若某站无法下载，多半需更新：`pip install -U yt-dlp` 或 `yt-dlp -U`。
