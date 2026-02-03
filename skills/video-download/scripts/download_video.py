#!/usr/bin/env python3
"""
根据视频链接下载 YouTube、B站等视频。封装 yt-dlp，用户给出 URL 即可下载。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_ytdlp(urls: list[str], out: str | None, audio_only: bool) -> int:
    """调用 yt-dlp 下载。"""
    cmd: list[str] = []
    if shutil.which("yt-dlp"):
        cmd.append("yt-dlp")
    else:
        cmd.extend([sys.executable, "-m", "yt_dlp"])
    if out:
        p = Path(out)
        if p.is_dir() or ("%" not in out and not p.suffix):
            cmd.extend(["-o", str(Path(out).resolve() / "%(title)s.%(ext)s")])
        else:
            cmd.extend(["-o", out])
    if audio_only:
        cmd.extend(["-x", "--audio-format", "mp3"])
    cmd.extend(urls)
    return subprocess.run(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="根据视频链接下载（YouTube/B站等），基于 yt-dlp。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "https://www.youtube.com/watch?v=xxx"
  %(prog)s "https://www.bilibili.com/video/BVxxx" -o ./downloads
  %(prog)s "https://..." --audio-only
        """,
    )
    parser.add_argument("url", nargs="+", help="视频页面链接，可多条")
    parser.add_argument("-o", "--output", metavar="DIR_OR_FILE", help="输出目录或文件名模板")
    parser.add_argument("--audio-only", action="store_true", help="仅下载并转为 mp3")
    args = parser.parse_args()
    return run_ytdlp(args.url, args.output, args.audio_only)


if __name__ == "__main__":
    sys.exit(main())
