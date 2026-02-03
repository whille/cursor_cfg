# video-download

根据视频链接下载 YouTube、B站、优酷等视频，基于 yt-dlp。

## 安装

```bash
pip install yt-dlp
brew install ffmpeg   # 可选，用于合并音视频、转 mp3
```

## 用法

```bash
# 下载到当前目录
python scripts/download_video.py "https://www.youtube.com/watch?v=xxx"

# 指定目录
python scripts/download_video.py "https://www.bilibili.com/video/BVxxx" -o ./downloads

# 仅音频 mp3
python scripts/download_video.py "https://..." --audio-only
```

也可直接使用 yt-dlp：

```bash
yt-dlp "https://..."
```

详细说明见 [SKILL.md](./SKILL.md)。
