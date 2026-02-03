# Ebook Converter Skill

A comprehensive Cursor Skill for converting ebooks between PDF, MOBI, and EPUB formats using Calibre.

## Features

- ✅ **Bidirectional Conversion**: PDF ↔ MOBI ↔ EPUB
- ✅ **Batch Processing**: Convert multiple files at once
- ✅ **Auto-detection**: Automatically determines output format
- ✅ **Metadata Support**: Set title, authors, language, etc.
- ✅ **Error Handling**: Clear error messages and validation

## Quick Start

### Installation

1. Ensure Calibre is installed:
   ```bash
   brew install calibre  # macOS
   ```

2. The skill is already installed in `~/.cursor/skills/ebook-converter/`

### Usage Examples

#### Command Line

```bash
# Convert PDF to EPUB
python ~/.cursor/skills/ebook-converter/scripts/convert.py input.pdf output.epub

# Convert EPUB to MOBI (auto-detect output)
python ~/.cursor/skills/ebook-converter/scripts/convert.py input.epub

# Batch convert all PDFs to EPUB
python ~/.cursor/skills/ebook-converter/scripts/convert.py \
    --batch --input-format pdf --output-format epub /path/to/files
```

#### Direct ebook-convert (Simpler)

```bash
# PDF to EPUB
ebook-convert input.pdf output.epub

# EPUB to MOBI
ebook-convert input.epub output.mobi

# MOBI to PDF
ebook-convert input.mobi output.pdf
```

#### Python API

```python
from pathlib import Path
from ebook_converter.scripts.convert import convert_ebook

# Convert PDF to EPUB
result = convert_ebook(Path("input.pdf"), Path("output.epub"))
print(f"Converted to: {result}")

# Auto-detect output format
result = convert_ebook(Path("input.epub"))  # Creates input.mobi
```

## Supported Formats

- **Input**: PDF, EPUB, MOBI, AZW3, FB2, LIT, LRF, PDB, RB, RTF, SNB, TCR, TXT, TXTZ, ZIP
- **Output**: PDF, EPUB, MOBI, AZW3, FB2, LIT, LRF, PDB, RB, RTF, SNB, TCR, TXT, TXTZ, ZIP

## Format Conversion Matrix

| From → To | PDF | EPUB | MOBI |
|-----------|-----|------|------|
| **PDF**   | -   | ✅   | ✅   |
| **EPUB**  | ✅  | -    | ✅   |
| **MOBI**  | ✅  | ✅   | -    |

## Advanced Options

```bash
# Convert with metadata
ebook-convert input.pdf output.epub \
    --title "Book Title" \
    --authors "Author Name" \
    --language zh

# PDF-specific options
ebook-convert input.pdf output.epub \
    --pdf-image-dpi 300 \
    --pdf-page-margin 10

# EPUB-specific options
ebook-convert input.epub output.mobi \
    --epub-version 3 \
    --epub-flatten
```

## Troubleshooting

### Calibre Not Found

```bash
# Check installation
which ebook-convert

# Install Calibre
brew install calibre  # macOS
```

### Conversion Quality Issues

- **PDF to EPUB/MOBI**: Quality depends on PDF structure
  - Text-based PDFs: Excellent
  - Scanned PDFs: May need OCR first
  - Complex layouts: May require manual adjustment

- **Best Practices**:
  - EPUB → MOBI: Best quality
  - For PDFs: Try PDF → EPUB → MOBI for better results

## Resources

- [Calibre Documentation](https://manual.calibre-ebook.com/)
- [ebook-convert Manual](https://manual.calibre-ebook.com/generated/en/ebook-convert.html)
- [Calibre Download](https://calibre-ebook.com/download)
