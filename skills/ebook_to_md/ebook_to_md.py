# -*- coding: utf-8 -*-
"""
ebook_to_md skill: convert PDF/PNG/JPEG/MOBI/EPUB to Markdown or HTML.
Supports Baidu OCR (default) or local Tesseract. Schema auto-inferred from run().
"""

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import base64
import io
import json
import logging
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytesseract  # type: ignore[import-untyped]
import requests
import fitz
from PIL import Image

try:
    import markdown
except ImportError:
    markdown = None  # type: ignore[misc, assignment]

try:
    import mistune
except ImportError:
    mistune = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)

# Cursor-style: schema inferred from run()
TOOL_DESCRIPTION = "将 PDF/图片/MOBI/EPUB 转为 Markdown 或 HTML，支持百度 OCR（默认）或本地 Tesseract"
TOOL_REQUIRED = ["input_path"]
PARAM_DESCRIPTIONS = {
    "input_path": "文档路径，支持 pdf/png/jpeg/mobi/epub；可为 base64 图片数据",
    "output_path": "输出文件路径（不指定则仅返回字符串）",
    "output_format": "输出格式：md（默认）或 html",
    "ocr_backend": "OCR 引擎：baidu（默认）或 local",
    "inline_images": "图片是否 base64 内联（仅 baidu+PDF）",
}

FIG_HEIGHT_PT = 260
API_BASE = "https://aip.baidubce.com"
IMG_SRC_PATTERN = re.compile(r'<img\s+src=["\']?([^"\'>\s]+)["\']?\s*/?>', re.IGNORECASE)

SUPPORTED_INPUT_EXTS = {".pdf", ".png", ".jpeg", ".jpg", ".mobi", ".epub"}
IMAGE_EXTS = {".png", ".jpeg", ".jpg"}


def _setup_tessdata() -> None:
    """设置 TESSDATA_PREFIX，优先项目 tessdata/ 或 skill tessdata/"""
    if os.environ.get("TESSDATA_PREFIX"):
        return
    root = Path(__file__).resolve().parents[2]
    for p in [root / "tessdata", Path(__file__).resolve().parent / "tessdata"]:
        if (p / "chi_sim.traineddata").exists():
            os.environ["TESSDATA_PREFIX"] = str(p) + os.sep
            logger.info("TESSDATA_PREFIX=%s", os.environ["TESSDATA_PREFIX"])
            return


def _detect_input_type(input_path: str) -> str:
    """Return: pdf, image, mobi, epub. For base64/data URI, return image."""
    if not input_path or not isinstance(input_path, str):
        return ""
    s = input_path.strip()
    if s.startswith("data:image") or (len(s) > 50 and re.match(r"^[A-Za-z0-9+/]+=*$", s)):
        return "image"
    p = Path(s)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext == ".mobi":
        return "mobi"
    if ext == ".epub":
        return "epub"
    return ""


def _convert_ebook_to_pdf(ebook_path: str) -> str:
    """Convert mobi/epub to PDF via Calibre ebook-convert. Returns path to temp PDF."""
    path = Path(ebook_path)
    if not path.exists():
        raise FileNotFoundError("文件不存在: {}".format(ebook_path))
    ext = path.suffix.lower()
    if ext not in (".mobi", ".epub"):
        raise ValueError("仅支持 mobi、epub 格式: {}".format(ext))

    try:
        result = subprocess.run(
            ["ebook-convert", str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError("ebook-convert 不可用")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        raise RuntimeError(
            "未检测到 Calibre。请安装: macOS brew install calibre, "
            "Linux apt-get install calibre。错误: {}".format(e)
        )

    fd, tmp_pdf = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        result = subprocess.run(
            ["ebook-convert", str(path), tmp_pdf],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError("ebook-convert 转换失败: {}".format(result.stderr or result.stdout))
        return tmp_pdf
    except Exception:
        if os.path.exists(tmp_pdf):
            try:
                os.remove(tmp_pdf)
            except OSError:
                pass
        raise


def _markdown_to_html(md_content: str) -> str:
    """Convert Markdown to HTML."""
    if markdown is not None:
        return markdown.markdown(md_content, extensions=["extra", "codehilite"])
    if mistune is not None:
        return mistune.markdown(md_content)
    return "<pre>{}</pre>".format(escape(md_content))


# ----- Baidu OCR helpers (from ocr skill) -----


def _get_access_token(api_key: str, secret_key: str) -> Optional[str]:
    try:
        url = "{}/oauth/2.0/token".format(API_BASE)
        params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
        resp = requests.post(url, params=params)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error("获取访问令牌失败: {}".format(str(e)))
        return None


def _read_image_file(image_path: str) -> Optional[str]:
    try:
        if image_path.startswith("data:image"):
            parts = image_path.split(",")
            if len(parts) > 1:
                return parts[1]
            return image_path
        base64_pattern = re.compile(r"^[A-Za-z0-9+/]+=*$")
        if len(image_path) > 50 and base64_pattern.match(image_path):
            return image_path
        if not Path(image_path).exists():
            if len(image_path) > 20 and base64_pattern.match(image_path):
                return image_path
            return None
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error("读取图片失败: {}".format(str(e)))
        return None


def _call_baidu_ocr_api(
    api_key: str, secret_key: str, image_base64: str, language_type: str = "CHN_ENG"
) -> Dict[str, Any]:
    try:
        access_token = _get_access_token(api_key, secret_key)
        if not access_token:
            return {"error_code": -1, "error_msg": "无法获取访问令牌"}
        url = "{}/rest/2.0/ocr/v1/general_basic".format(API_BASE)
        params = {"access_token": access_token}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "image": image_base64,
            "language_type": language_type,
            "detect_direction": "true",
            "paragraph": "true",
        }
        resp = requests.post(url, params=params, headers=headers, data=data)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("OCR API 请求失败: {}".format(str(e)))
        return {"error_code": -1, "error_msg": str(e)}


def _extract_text_from_baidu_result(result: Dict[str, Any]) -> str:
    if "error_code" in result and result.get("error_code", 0) != 0:
        return "OCR识别失败: {}".format(result.get("error_msg", "未知错误"))
    words = result.get("words_result", [])
    if not words:
        return "未识别到文字"
    return "\n".join(item.get("words", "") for item in words)


def _format_image_markdown_paragraphs(content: str) -> str:
    """对图片 OCR 输出添加 Markdown 分段（标题、段落空行）。"""
    if not content or not content.strip():
        return content
    lines = content.split("\n")
    if not lines:
        return content
    out = []
    # 首行若为短标题（2～12 字、无句末标点），转为 ## 标题
    first = lines[0].strip()
    if first and len(first) <= 12 and not re.search(r"[。？！.?!：:]\s*$", first):
        out.append("## " + first)
        out.append("")
        start = 1
    else:
        start = 0
    # 在每段以 “ 开头的对话前插入空行（分段）
    for i in range(start, len(lines)):
        line = lines[i]
        if line.strip().startswith("\u201c") and out and out[-1] != "":
            out.append("")
        out.append(line)
    return "\n".join(out).rstrip()


def _submit_parser_task(access_token: str, file_path: str, file_name: str) -> str:
    with open(file_path, "rb") as f:
        file_data = base64.b64encode(f.read()).decode("utf-8")
    url = "{}/rest/2.0/brain/online/v2/parser/task".format(API_BASE)
    params = {"access_token": access_token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"file_data": file_data, "file_name": file_name}
    resp = requests.post(url, params=params, headers=headers, data=data)
    if resp.status_code != 200:
        raise RuntimeError("提交任务失败: HTTP {} - {}".format(resp.status_code, resp.text))
    j = resp.json()
    if j.get("error_code", 0) != 0:
        raise RuntimeError(
            "百度 API 错误: error_code={}, error_msg={}".format(j.get("error_code"), j.get("error_msg", ""))
        )
    task_id = (j.get("result") or {}).get("task_id")
    if not task_id:
        raise RuntimeError("响应中无 task_id")
    return task_id


def _query_parser_result(access_token: str, task_id: str) -> dict:
    url = "{}/rest/2.0/brain/online/v2/parser/task/query".format(API_BASE)
    params = {"access_token": access_token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"task_id": task_id}
    resp = requests.post(url, params=params, headers=headers, data=data)
    if resp.status_code != 200:
        raise RuntimeError("查询失败: HTTP {}".format(resp.status_code))
    j = resp.json()
    if j.get("error_code", 0) != 0:
        raise RuntimeError("百度 API 错误: {}".format(j.get("error_msg", "")))
    return j.get("result") or {}


def _download_markdown(markdown_url: str) -> str:
    resp = requests.get(markdown_url)
    resp.raise_for_status()
    return resp.text


def _download_parse_result_json(parse_result_url: str) -> dict:
    resp = requests.get(parse_result_url)
    resp.raise_for_status()
    return json.loads(resp.content.decode("utf-8", errors="replace"))


def _detect_image_mime(raw: bytes) -> str:
    if raw[:2] == b"\xff\xd8":
        return "image/jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if raw[:2] == b"BM":
        return "image/bmp"
    if len(raw) > 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _fetch_image_raw(url: str):
    resp = requests.get(url)
    resp.raise_for_status()
    raw = resp.content
    mime = _detect_image_mime(raw)
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/webp": ".webp",
    }
    return raw, ext_map.get(mime, ".jpg")


def _fetch_image_as_base64(url: str) -> str:
    raw, _ = _fetch_image_raw(url)
    return "data:{};base64,{}".format(_detect_image_mime(raw), base64.b64encode(raw).decode("utf-8"))


def _table_to_html(table: dict) -> str:
    cells = table.get("cells") or []
    matrix = table.get("matrix")
    if not cells or not matrix:
        return table.get("markdown", "")
    rows = len(matrix)
    cols = max(len(r) for r in matrix) if matrix else 0
    if rows == 0 or cols == 0:
        return table.get("markdown", "")

    def get_colspan(mat, r, c):
        idx_val = mat[r][c]
        count = 1
        for cc in range(c + 1, len(mat[r])):
            if mat[r][cc] == idx_val:
                count += 1
            else:
                break
        return count

    def get_rowspan(mat, r, c):
        idx_val = mat[r][c]
        count = 1
        for rr in range(r + 1, rows):
            if c < len(mat[rr]) and mat[rr][c] == idx_val:
                count += 1
            else:
                break
        return count

    rowspan_at = {}
    for r in range(rows):
        for c in range(len(matrix[r])):
            if (r, c) in rowspan_at:
                continue
            idx_val = matrix[r][c]
            for rr in range(r + 1, r + get_rowspan(matrix, r, c)):
                for cc in range(c, min(c + get_colspan(matrix, r, c), len(matrix[rr]) if rr < rows else 0)):
                    if rr < rows:
                        rowspan_at[(rr, cc)] = True

    html = ['<table style="text-align:center">']
    for r in range(rows):
        html.append("<tr>")
        c = 0
        while c < len(matrix[r]):
            if (r, c) in rowspan_at:
                c += 1
                continue
            idx_val = matrix[r][c]
            cell = cells[idx_val] if idx_val < len(cells) else {}
            text = (cell.get("text") or "").strip()
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            text = text.replace('"', "&quot;").replace("\n", "<br>")
            rspan = get_rowspan(matrix, r, c)
            cspan = get_colspan(matrix, r, c)
            attrs = ['style="text-align:center"']
            if rspan > 1:
                attrs.append('rowspan="{}"'.format(rspan))
            if cspan > 1:
                attrs.append('colspan="{}"'.format(cspan))
            html.append("<td {}>{}</td>".format(" ".join(attrs), text or ""))
            c += cspan
        html.append("</tr>")
    html.append("</table>")
    return "\n".join(html)


def _replace_tables_with_html(md_content: str, parse_data: dict) -> str:
    tables = []
    for p in sorted(parse_data.get("pages", []), key=lambda x: x.get("page_num", 0)):
        tables.extend(p.get("tables") or [])
    if not tables:
        return md_content
    table_pattern = re.compile(r"(\|[^\n]+\|\s*\n)+", re.MULTILINE)
    idx = [0]

    def repl(m):
        if idx[0] >= len(tables):
            return m.group(0)
        html = _table_to_html(tables[idx[0]])
        idx[0] += 1
        return html + "\n"

    return table_pattern.sub(repl, md_content)


def _build_markdown_from_pages(pages: List[dict]) -> str:
    parts = []
    for p in sorted(pages, key=lambda x: x.get("page_num", 0)):
        text = p.get("text", "")
        if text and text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def _normalize_figure_to_markdown(md_content: str) -> str:
    figure_pattern = re.compile(
        r"<figure>\s*(?:!\[\]\(([^)]+)\)|<\s*img[^>]+>)\s*<figcaption>([^<]*)</figcaption>.*?</figure>",
        re.IGNORECASE | re.DOTALL,
    )

    def _repl(m):
        path = m.group(1)
        cap = (m.group(2) or "").strip()
        if not path.startswith("./") and not path.startswith("data:"):
            path = "./" + path
        return "![{}]({})".format(cap, path)

    return figure_pattern.sub(_repl, md_content)


def _inline_images_as_base64(md_content: str) -> str:
    def repl(m):
        url = m.group(1).strip()
        try:
            return "![]({})".format(_fetch_image_as_base64(url))
        except Exception as e:
            return m.group(0) + "  <!-- 下载失败: {} -->".format(e)

    return IMG_SRC_PATTERN.sub(repl, md_content)


def _inline_images_as_local(md_content: str, output_path: Path) -> str:
    out_dir = output_path.parent
    images_dir = output_path.stem + "_images"
    images_path = out_dir / images_dir
    images_path.mkdir(parents=True, exist_ok=True)
    rel_prefix = "./" + images_dir + "/"
    idx = [0]

    def repl(m):
        url = m.group(1).strip()
        try:
            raw, ext = _fetch_image_raw(url)
            fname = "{}{}".format(idx[0], ext)
            idx[0] += 1
            (images_path / fname).write_bytes(raw)
            return "![]({})".format(rel_prefix + fname)
        except Exception as e:
            return m.group(0) + "  <!-- 下载失败: {} -->".format(e)

    return IMG_SRC_PATTERN.sub(repl, md_content)


@dataclass
class _BaiduComplexConfig:
    api_key: str
    secret_key: str
    output_path: Optional[str] = None
    inline_images: bool = False


def _execute_baidu_complex(config: _BaiduComplexConfig, file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return "错误: 文件不存在: {}".format(file_path)
    output_path_obj = Path(config.output_path) if config.output_path else path.with_suffix(".md")
    access_token = _get_access_token(config.api_key, config.secret_key)
    if not access_token:
        return "错误: 无法获取访问令牌，请检查 API 密钥"
    try:
        task_id = _submit_parser_task(access_token, str(path), path.name)
    except Exception as e:
        return "错误: {}".format(str(e))
    max_wait = 120
    poll_interval = 5
    elapsed = 0
    status = None
    result = {}
    while elapsed < max_wait:
        try:
            result = _query_parser_result(access_token, task_id)
        except Exception as e:
            return "错误: {}".format(str(e))
        status = result.get("status")
        if status == "success":
            break
        if status == "failed":
            return "错误: 文档解析失败: {}".format(result.get("task_error", "未知错误"))
        time.sleep(poll_interval)
        elapsed += poll_interval
    if status != "success":
        return "错误: 超时，任务未在 {} 秒内完成".format(max_wait)
    markdown_url = result.get("markdown_url")
    parse_result_url = result.get("parse_result_url")
    parse_data = None
    if parse_result_url:
        try:
            parse_data = _download_parse_result_json(parse_result_url)
        except Exception as e:
            logger.warning("下载 parse_result_url 失败: {}".format(e))
    md_content = None
    if markdown_url:
        try:
            md_content = _download_markdown(markdown_url)
        except Exception as e:
            logger.warning("下载 markdown 失败: {}".format(e))
    if md_content is None or not md_content.strip():
        if parse_data:
            md_content = _build_markdown_from_pages(parse_data.get("pages", []))
        else:
            return "错误: 无法获取解析结果"
    if parse_data:
        md_content = _replace_tables_with_html(md_content, parse_data)
    if "img src=" in md_content or 'img src="' in md_content:
        if config.inline_images:
            md_content = _inline_images_as_base64(md_content)
        else:
            md_content = _inline_images_as_local(md_content, output_path_obj)
    if "<figure>" in md_content or "<figcaption>" in md_content:
        md_content = _normalize_figure_to_markdown(md_content)
    return md_content


# ----- Local OCR: _PdfOcrImpl logic (from pdf_ocr_to_markdown) -----


class _LocalPdfOcrImpl:
    """Local Tesseract OCR for PDF."""

    def _ocr_pages(self, pdf_path: str, scale: float = 2.0) -> List[Tuple[str, Any]]:
        _setup_tessdata()
        doc = fitz.open(pdf_path)
        results = []
        mat = fitz.Matrix(scale, scale)
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="chi_sim")
            results.append((text, img))
        doc.close()
        return results

    def _extract_figures(self, pdf_path: str, output_stem: str, scale: float = 2.0) -> Dict[str, str]:
        _setup_tessdata()
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(scale, scale)
        fig_height_px = FIG_HEIGHT_PT * scale
        out_dir = Path(output_stem).parent / (Path(output_stem).stem + "_images")
        out_dir.mkdir(parents=True, exist_ok=True)
        figures = {}
        line_nums = data = None
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            data = pytesseract.image_to_data(img, lang="chi_sim", output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            line_nums = data.get("line_num", [0] * n_boxes)
            for i in range(n_boxes):
                txt = (data["text"][i] or "").strip()
                fig_num = None
                if txt == "图":
                    for j in range(i + 1, n_boxes):
                        if line_nums[j] != line_nums[i]:
                            break
                        next_txt = (data["text"][j] or "").strip()
                        if next_txt.isdigit():
                            fig_num = next_txt
                            break
                elif txt and txt[0] == "图" and len(txt) > 1:
                    m = re.search(r"图\s*(\d+)", txt)
                    if m:
                        fig_num = m.group(1)
                if not fig_num or fig_num in figures:
                    continue
                left = data["left"][i]
                top = data["top"][i]
                width = data["width"][i]
                height = data["height"][i]
                if txt == "图":
                    for j in range(i + 1, n_boxes):
                        if line_nums[j] != line_nums[i]:
                            break
                        next_txt = (data["text"][j] or "").strip()
                        if next_txt == fig_num:
                            l2, t2, w2, h2 = (
                                data["left"][j],
                                data["top"][j],
                                data["width"][j],
                                data["height"][j],
                            )
                            left = min(left, l2)
                            top = min(top, t2)
                            width = max(left + width, l2 + w2) - left
                            height = max(top + height, t2 + h2) - top
                            break
                crop_top = max(0, int(top - fig_height_px))
                crop_left = max(0, int(left) - 20)
                crop_right = min(img.width, int(left) + int(width) + 20)
                crop_bottom = int(top) + int(height) + 10
                crop_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                fn = "fig{}.png".format(fig_num)
                out_path = out_dir / fn
                crop_img.save(out_path)
                rel = (Path(output_stem).stem + "_images") + "/" + fn
                figures[fig_num] = "./" + rel
        doc.close()
        return figures

    def _parse_tables(self, text: str) -> str:
        lines = text.strip().split("\n")
        output = []
        buf = []

        def _flush_table():
            if len(buf) < 2:
                for row in buf:
                    output.append(" ".join(row))
                return
            col_count = max(len(row) for row in buf)
            for row in buf:
                while len(row) < col_count:
                    row.append("")
            sep = ["---"] * col_count
            table = "| " + " | ".join(buf[0]) + " |\n"
            table += "| " + " | ".join(sep) + " |\n"
            for row in buf[1:]:
                table += "| " + " | ".join(row) + " |\n"
            output.append(table.rstrip())

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if buf:
                    _flush_table()
                    buf = []
                output.append("")
                continue
            parts = re.split(r"\s{2,}|\t|\|", stripped)
            parts = [p.strip() for p in parts if p.strip()]
            is_table_row = len(parts) >= 3 and (
                any(re.search(r"[\d～~\-\s]+", p) for p in parts) or any("—" in p or "－" in p for p in parts)
            )
            if is_table_row:
                buf.append(parts)
            else:
                if buf:
                    _flush_table()
                    buf = []
                output.append(stripped)
        if buf:
            _flush_table()
        return "\n".join(output)

    def _insert_figure_refs(self, markdown: str, figures: Dict[str, str]) -> str:
        if not figures:
            return markdown
        for fig_num, rel_path in figures.items():
            pattern = re.compile(
                r"([（(]?\s*图\s*" + re.escape(fig_num) + r"\s*[)）]?)",
                re.IGNORECASE,
            )
            alt = "图{}".format(fig_num)
            img_md = "\n\n![{}]({})\n\n".format(alt, rel_path)

            def repl(m):
                return m.group(0) + img_md

            markdown = pattern.sub(repl, markdown, count=1)
        return markdown

    def execute_pdf(self, pdf_path: str, output_path: Optional[str]) -> Dict[str, Any]:
        path = Path(pdf_path)
        pages_data = self._ocr_pages(str(path))
        full_text = "\n\n".join(t[0] for t in pages_data)
        page_count = len(pages_data)
        if not full_text.strip():
            return {"success": False, "error": "OCR 未识别到文字", "page_count": page_count}
        output_stem = str(Path(output_path).with_suffix("")) if output_path else str(path.with_suffix(""))
        figures = self._extract_figures(str(path), output_stem)
        markdown = self._parse_tables(full_text)
        markdown = self._insert_figure_refs(markdown, figures)
        markdown = markdown.strip()
        return {
            "success": True,
            "markdown": markdown,
            "page_count": page_count,
            "figure_count": len(figures),
        }


def _ocr_image_local(image_path: str) -> str:
    """Tesseract OCR for single image. Handles path or base64."""
    _setup_tessdata()
    image_base64 = _read_image_file(image_path)
    if not image_base64:
        raise ValueError("无法读取图片文件")
    try:
        raw = base64.b64decode(image_base64)
    except Exception:
        if Path(image_path).exists():
            with open(image_path, "rb") as f:
                raw = f.read()
        else:
            raise ValueError("无法解码图片数据")
    img = Image.open(io.BytesIO(raw))
    if img.mode != "RGB":
        img = img.convert("RGB")
    return pytesseract.image_to_string(img, lang="chi_sim")


# ----- Main router -----


class _EbookToMdImpl:
    """Unified ebook/image to Markdown or HTML."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        params = kwargs.get("parameters", kwargs) if isinstance(kwargs.get("parameters"), dict) else kwargs
        input_path = params.get("input_path") or kwargs.get("input_path")
        output_path = params.get("output_path") or kwargs.get("output_path")
        output_format = (params.get("output_format") or kwargs.get("output_format") or "md").lower()
        ocr_backend = (params.get("ocr_backend") or kwargs.get("ocr_backend") or "baidu").lower()
        inline_images = params.get("inline_images", kwargs.get("inline_images", False))

        if not input_path:
            return {"success": False, "error": "input_path 不能为空"}

        input_type = _detect_input_type(input_path)
        if not input_type:
            return {"success": False, "error": "不支持的格式，请使用 pdf/png/jpeg/mobi/epub"}

        is_path = not (
            input_path.startswith("data:")
            or (len(input_path) > 50 and re.match(r"^[A-Za-z0-9+/]+=*$", input_path))
        )
        if is_path and not Path(input_path).exists():
            return {"success": False, "error": "文件不存在: {}".format(input_path)}

        if input_type in ("mobi", "epub"):
            try:
                pdf_path = _convert_ebook_to_pdf(input_path)
                input_path = pdf_path
                input_type = "pdf"
                _temp_ebook_pdf = pdf_path
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            _temp_ebook_pdf = None

        _local_page_count = None
        _local_figure_count = None
        try:
            if input_type == "image":
                if ocr_backend == "baidu":
                    api_key = os.getenv("BAIDU_OCR_API_KEY")
                    secret_key = os.getenv("BAIDU_OCR_SECRET_KEY")
                    image_base64 = _read_image_file(input_path)
                    if not image_base64:
                        return {"success": False, "error": "无法读取图片"}
                    result = _call_baidu_ocr_api(api_key, secret_key, image_base64)
                    text = _extract_text_from_baidu_result(result)
                    if "error_code" in result and result.get("error_code", 0) != 0:
                        return {"success": False, "error": text}
                    content = text
                else:
                    content = _ocr_image_local(input_path)
                content = content.strip()
                if not content:
                    return {"success": False, "error": "未识别到文字"}
                markdown = _format_image_markdown_paragraphs(content)

            elif input_type == "pdf":
                if ocr_backend == "baidu":
                    api_key = os.getenv("BAIDU_OCR_API_KEY")
                    secret_key = os.getenv("BAIDU_OCR_SECRET_KEY")
                    baidu_config = _BaiduComplexConfig(
                        api_key=api_key,
                        secret_key=secret_key,
                        output_path=output_path,
                        inline_images=inline_images,
                    )
                    md_content = _execute_baidu_complex(baidu_config, input_path)
                    if md_content.startswith("错误:"):
                        return {"success": False, "error": md_content}
                    markdown = md_content
                else:
                    impl = _LocalPdfOcrImpl()
                    local_result = impl.execute_pdf(input_path, output_path)
                    if not local_result.get("success"):
                        return local_result
                    markdown = local_result["markdown"]
                    _local_page_count = local_result.get("page_count")
                    _local_figure_count = local_result.get("figure_count")
            else:
                return {"success": False, "error": "不支持的输入类型"}

            if output_format == "html":
                final_content = _markdown_to_html(markdown)
                out_ext = ".html"
            else:
                final_content = markdown
                out_ext = ".md"

            written_path = None
            if output_path:
                out = Path(output_path)
                if out.suffix.lower() not in (".md", ".html"):
                    out = out.with_suffix(out_ext)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(final_content, encoding="utf-8")
                written_path = str(out.resolve())

            response = {
                "success": True,
                "markdown": markdown,
                "content": final_content,
                "output_format": output_format,
                "message": "转换成功",
            }
            if written_path:
                response["output_path"] = written_path
            if _local_page_count is not None:
                response["page_count"] = _local_page_count
            if _local_figure_count is not None:
                response["figure_count"] = _local_figure_count
            return response

        finally:
            if _temp_ebook_pdf and os.path.exists(_temp_ebook_pdf):
                try:
                    os.remove(_temp_ebook_pdf)
                except OSError:
                    pass


def run(
    *,
    input_path: str = "",
    output_path: str = None,
    output_format: str = "md",
    ocr_backend: str = "baidu",
    inline_images: bool = False,
    **kwargs,
) -> str:
    """Execute ebook_to_md and return str."""
    params = kwargs.get("parameters", kwargs) if isinstance(kwargs.get("parameters"), dict) else kwargs
    input_path = params.get("input_path") or input_path
    output_path = params.get("output_path") or output_path
    output_format = (params.get("output_format") or output_format or "md").lower()
    ocr_backend = (params.get("ocr_backend") or ocr_backend or "baidu").lower()
    inline_images = params.get("inline_images", inline_images)

    if not input_path:
        return "错误: input_path 不能为空"
    try:
        impl = _EbookToMdImpl()
        result = impl.execute(
            input_path=input_path,
            output_path=output_path,
            output_format=output_format,
            ocr_backend=ocr_backend,
            inline_images=inline_images,
        )
        if result.get("success"):
            msg = "转换成功"
            if result.get("output_path"):
                msg += "，已写入: {}".format(result["output_path"])
            content = result.get("content", result.get("markdown", ""))
            if content:
                preview = content[:500].strip() + ("..." if len(content) > 500 else "")
                msg += "\n\n预览:\n{}".format(preview)
            return msg
        return "错误: {}".format(result.get("error", result.get("message", "转换失败")))
    except ImportError:
        return "错误: 请安装依赖: pip install pymupdf pytesseract Pillow requests"
    except Exception as e:
        logger.exception("ebook_to_md 失败: %s", e)
        return "错误: {}".format(str(e))
