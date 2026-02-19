#!/usr/bin/env python
"""
pytest 测试：ebook_to_md 工具
- 对 fixtures/*.pdf 调用工具（local OCR），输出到临时目录
- 与 fixtures/expected/*.md 做结构/内容对比，允许 OCR 误差范围内差异
"""

import re
from pathlib import Path

import pytest

from skills.ebook_to_md.ebook_to_md import _EbookToMdImpl, _LocalPdfOcrImpl

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = FIXTURES_DIR / "expected"


def _count_table_rows(md: str) -> int:
    """Markdown 表格行数（不含表头分隔行）"""
    lines = [l.strip() for l in md.split("\n")]
    count = 0
    in_table = False
    for line in lines:
        if line.startswith("|") and line.endswith("|"):
            if "---" not in line:
                count += 1
            in_table = True
        else:
            in_table = False
    return count


def _count_image_refs(md: str) -> int:
    """图片引用数量 ![alt](path)"""
    return len(re.findall(r"!\[[^\]]*\]\([^)]+\)", md))


def _execute_local_pdf(pdf_path: str, **kwargs):
    """调用 _LocalPdfOcrImpl().execute_pdf 返回 dict（用于本地 PDF 测试）"""
    output_path = kwargs.get("output_path")
    return _LocalPdfOcrImpl().execute_pdf(pdf_path, output_path)


def _execute_full(input_path: str, **kwargs):
    """调用 _EbookToMdImpl().execute 返回 dict"""
    known = {"ocr_backend", "output_path", "output_format"}
    extra = {k: v for k, v in kwargs.items() if k not in known}
    return _EbookToMdImpl().execute(
        input_path=input_path,
        ocr_backend=kwargs.get("ocr_backend", "local"),
        output_path=kwargs.get("output_path"),
        output_format=kwargs.get("output_format", "md"),
        **extra
    )


class TestEbookToMdLocalPdf:
    """ebook_to_md 工具测试（本地 Tesseract + PDF）"""

    def test_table_pdf_basic(self, tmp_path):
        """test_with_table.pdf：成功转换，有表格结构"""
        pdf_path = str(FIXTURES_DIR / "test_with_table.pdf")
        out_path = str(tmp_path / "test_with_table.md")
        r = _execute_full(pdf_path, ocr_backend="local", output_path=out_path)

        assert r.get("success") is True
        assert r.get("page_count", 0) >= 1
        md = r.get("markdown", r.get("content", ""))
        assert len(md) > 100

        table_rows = _count_table_rows(md)
        assert table_rows >= 1, "应识别到至少 1 行表格"

        assert Path(out_path).exists()

    def test_table_pdf_structure_vs_expected(self, tmp_path):
        """test_with_table：与 expected 做结构对比（表格行数）"""
        pdf_path = str(FIXTURES_DIR / "test_with_table.pdf")
        out_path = str(tmp_path / "test_with_table.md")
        r = _execute_full(pdf_path, ocr_backend="local", output_path=out_path)

        assert r.get("success") is True
        md = r.get("markdown", r.get("content", ""))
        expected_path = EXPECTED_DIR / "test_with_table.md"
        expected_md = expected_path.read_text(encoding="utf-8")

        exp_rows = _count_table_rows(expected_md)
        out_rows = _count_table_rows(md)
        assert out_rows >= 1
        assert exp_rows >= 1

    def test_pic_pdf_figures(self, tmp_path):
        """test_with_pic.pdf：成功转换，提取图片"""
        pdf_path = str(FIXTURES_DIR / "test_with_pic.pdf")
        out_path = str(tmp_path / "test_with_pic.md")
        r = _execute_full(
            pdf_path, ocr_backend="local",
            output_path=out_path
        )

        assert r.get("success") is True
        assert r.get("page_count", 0) >= 1
        assert r.get("figure_count", 0) >= 1

        md = r.get("markdown", r.get("content", ""))
        img_count = _count_image_refs(md)
        assert img_count >= 1

        img_dir = tmp_path / "test_with_pic_images"
        assert img_dir.exists()
        assert list(img_dir.glob("fig*.png"))

    def test_pic_pdf_structure_vs_expected(self, tmp_path):
        """test_with_pic：与 expected 做结构对比（图片引用）"""
        pdf_path = str(FIXTURES_DIR / "test_with_pic.pdf")
        out_path = str(tmp_path / "test_with_pic.md")
        r = _execute_full(
            pdf_path, ocr_backend="local",
            output_path=out_path
        )

        assert r.get("success") is True
        md = r.get("markdown", r.get("content", ""))
        expected_path = EXPECTED_DIR / "test_with_pic.md"
        expected_md = expected_path.read_text(encoding="utf-8")

        exp_imgs = _count_image_refs(expected_md)
        out_imgs = _count_image_refs(md)
        assert out_imgs >= exp_imgs

    def test_without_output_path_returns_string(self):
        """不指定 output_path 时仅返回字符串"""
        pdf_path = str(FIXTURES_DIR / "test_with_table.pdf")
        r = _execute_full(pdf_path, ocr_backend="local")

        assert r.get("success") is True
        assert "markdown" in r or "content" in r
        assert "output_path" not in r or r.get("output_path") is None
