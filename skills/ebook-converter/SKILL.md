---
name: ebook-converter
description: Convert ebooks between PDF, MOBI, and EPUB formats using Calibre's ebook-convert. Supports bidirectional conversion between all three formats and batch processing. Use when you need to convert ebook files between PDF, MOBI, and EPUB formats.
---

# Ebook Format Converter

Comprehensive skill for converting ebooks between PDF, MOBI, and EPUB formats using Calibre's proven conversion engine.

## Overview

This skill provides a complete solution for ebook format conversion, supporting all combinations:
- **PDF ↔ MOBI**: Convert PDF files to MOBI format and vice versa
- **PDF ↔ EPUB**: Convert PDF files to EPUB format and vice versa
- **MOBI ↔ EPUB**: Convert MOBI files to EPUB format and vice versa

Based on Calibre's `ebook-convert` command, the industry-standard tool for ebook conversion.

## Quick Start

### Prerequisites

Calibre must be installed:
- **macOS**: `brew install calibre`
- **Linux**: `sudo apt-get install calibre` or `sudo yum install calibre`
- **Windows**: Download from https://calibre-ebook.com/download

Verify installation:
```bash
which ebook-convert
# Should output: /usr/local/bin/ebook-convert (or similar)
```

### Basic Usage

```bash
# Convert PDF to EPUB
ebook-convert input.pdf output.epub

# Convert EPUB to MOBI
ebook-convert input.epub output.mobi

# Convert MOBI to PDF
ebook-convert input.mobi output.pdf
```

## Supported Conversions

### All Format Combinations

| From → To | Command Example |
|-----------|----------------|
| PDF → EPUB | `ebook-convert file.pdf file.epub` |
| PDF → MOBI | `ebook-convert file.pdf file.mobi` |
| EPUB → PDF | `ebook-convert file.epub file.pdf` |
| EPUB → MOBI | `ebook-convert file.epub file.mobi` |
| MOBI → PDF | `ebook-convert file.mobi file.pdf` |
| MOBI → EPUB | `ebook-convert file.mobi file.epub` |

## Usage Examples

### Example 1: Single File Conversion

```bash
# Convert a PDF to EPUB
ebook-convert "周易.pdf" "周易.epub"

# Convert EPUB to MOBI
ebook-convert "zhouyi.epub" "zhouyi.mobi"
```

### Example 2: Batch Conversion (Bash)

```bash
# Convert all PDF files in current directory to EPUB
for file in *.pdf; do
    ebook-convert "$file" "${file%.pdf}.epub"
done

# Convert all EPUB files to MOBI
for file in *.epub; do
    ebook-convert "$file" "${file%.epub}.mobi"
done

# Convert all MOBI files to PDF
for file in *.mobi; do
    ebook-convert "$file" "${file%.mobi}.pdf"
done
```

### Example 3: Python Wrapper Script

```python
#!/usr/bin/env python3
"""Ebook format converter supporting PDF, MOBI, and EPUB."""

import subprocess
import sys
from pathlib import Path

def convert_ebook(input_file: Path, output_file: Path = None) -> Path:
    """
    Convert ebook between PDF, MOBI, and EPUB formats.

    Args:
        input_file: Path to input file (PDF, MOBI, or EPUB)
        output_file: Optional output path. If None, auto-generates based on input.

    Returns:
        Path to converted file

    Raises:
        FileNotFoundError: If input file doesn't exist
        subprocess.CalledProcessError: If conversion fails
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Auto-generate output filename if not provided
    if output_file is None:
        ext_map = {
            '.pdf': '.epub',
            '.epub': '.mobi',
            '.mobi': '.pdf'
        }
        output_file = input_file.with_suffix(ext_map.get(input_file.suffix.lower(), '.epub'))

    # Run conversion
    subprocess.run(
        ['ebook-convert', str(input_file), str(output_file)],
        check=True
    )

    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_file> [output_file]")
        print("Supported formats: PDF, MOBI, EPUB")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        result = convert_ebook(input_path, output_path)
        print(f"✅ Converted: {result}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### Example 4: Advanced Conversion with Options

```bash
# Convert with custom metadata
ebook-convert input.pdf output.epub \
    --title "Custom Title" \
    --authors "Author Name" \
    --language zh

# Convert with specific page range (PDF to EPUB)
ebook-convert input.pdf output.epub --page-range 1-50

# Convert with quality settings (for image-heavy PDFs)
ebook-convert input.pdf output.epub \
    --pdf-image-dpi 300 \
    --embed-font-family "Arial"
```

## Format-Specific Notes

### PDF Conversion
- **PDF → EPUB/MOBI**: Quality depends on PDF structure
  - Text-based PDFs convert well
  - Scanned/image-based PDFs may require OCR
  - Complex layouts may need manual adjustment
- **EPUB/MOBI → PDF**: Generally produces good results

### EPUB Conversion
- **EPUB → MOBI**: Excellent conversion quality
- **EPUB → PDF**: High-quality output, preserves formatting
- **MOBI/PDF → EPUB**: Good results, EPUB is a flexible format

### MOBI Conversion
- **MOBI → EPUB**: Excellent conversion (MOBI is based on EPUB)
- **MOBI → PDF**: Good quality
- **PDF/EPUB → MOBI**: Optimized for Kindle devices

## Advantages

- ✅ **Universal Support**: All format combinations (PDF↔MOBI↔EPUB)
- ✅ **No Dependencies**: Uses system-installed Calibre
- ✅ **Industry Standard**: Based on Calibre's proven conversion engine
- ✅ **High Quality**: Best-in-class conversion results
- ✅ **Flexible**: Supports many additional formats (AZW3, FB2, LIT, etc.)
- ✅ **Batch Processing**: Easy to convert multiple files

## Limitations

- Requires Calibre to be installed
- PDF to EPUB/MOBI quality varies with PDF structure
- Complex PDF layouts may not convert perfectly
- Some proprietary formats have limited support

## Troubleshooting

### Command Not Found

```bash
# Check if Calibre is installed
which ebook-convert

# Install if missing
brew install calibre  # macOS
sudo apt-get install calibre  # Debian/Ubuntu
sudo yum install calibre  # RHEL/CentOS
```

### Conversion Fails

1. **Check file integrity**: Verify input file is not corrupted
2. **Check permissions**: Ensure read access to input, write access to output directory
3. **Try intermediate format**: Convert PDF → EPUB → MOBI for better results
4. **Check file format**: Verify file extension matches actual format

### Poor Conversion Quality

**PDF Issues:**
- Scanned PDFs: Consider OCR tools first
- Complex layouts: May need manual editing
- Image-heavy PDFs: Try `--pdf-image-dpi` option

**General Tips:**
- EPUB to MOBI typically produces best results
- For PDFs, try converting to EPUB first, then to target format
- Use Calibre GUI for advanced options and preview

### Large File Sizes

```bash
# Compress images during conversion
ebook-convert input.pdf output.epub --compress-output-size

# Reduce image quality (for smaller files)
ebook-convert input.epub output.mobi --mobi-file-type both
```

## Advanced Options

### Common Conversion Options

```bash
# Set metadata
ebook-convert input.epub output.mobi \
    --title "Book Title" \
    --authors "Author" \
    --publisher "Publisher" \
    --isbn "1234567890"

# Language settings
ebook-convert input.pdf output.epub --language zh-CN

# Page range (for PDFs)
ebook-convert input.pdf output.epub --page-range 10-50

# Image settings
ebook-convert input.pdf output.epub \
    --pdf-image-dpi 300 \
    --embed-font-family "Times New Roman"
```

### Format-Specific Options

**PDF Options:**
- `--pdf-image-dpi`: Image resolution (default: 72)
- `--pdf-page-margin`: Page margins
- `--pdf-add-toc`: Add table of contents

**EPUB Options:**
- `--epub-version`: EPUB version (2 or 3)
- `--epub-flatten`: Flatten file structure
- `--epub-cover`: Cover image path

**MOBI Options:**
- `--mobi-file-type`: MOBI file type (old, both, new)
- `--mobi-keep-original-images`: Preserve original images
- `--mobi-toc-at-start`: Place TOC at start

## Resources

- **Calibre Documentation**: https://manual.calibre-ebook.com/
- **ebook-convert Manual**: https://manual.calibre-ebook.com/generated/en/ebook-convert.html
- **Calibre Download**: https://calibre-ebook.com/download
- **Format Support**: https://manual.calibre-ebook.com/conversion.html

## Related Skills

- **pdf-epub-to-mobi-lightweight**: Lightweight version for PDF/EPUB to MOBI only
