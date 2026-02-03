#!/usr/bin/env python3
"""
Ebook format converter supporting PDF, MOBI, and EPUB.
Converts between all three formats bidirectionally.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


# Supported formats mapping
SUPPORTED_FORMATS = {
    ".pdf": "PDF",
    ".epub": "EPUB",
    ".mobi": "MOBI",
    ".azw3": "AZW3",
    ".fb2": "FB2",
    ".lit": "LIT",
    ".lrf": "LRF",
    ".pdb": "PDB",
    ".rb": "RB",
    ".rtf": "RTF",
    ".snb": "SNB",
    ".tcr": "TCR",
    ".txt": "TXT",
    ".txtz": "TXTZ",
    ".zip": "ZIP",
}


def check_calibre_installed() -> bool:
    """Check if Calibre's ebook-convert is available."""
    try:
        subprocess.run(["ebook-convert", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_output_format(input_path: Path, target_format: Optional[str] = None) -> str:
    """
    Determine output format from input file or target format.

    Args:
        input_path: Path to input file
        target_format: Optional target format (pdf, epub, mobi)

    Returns:
        Output file extension (e.g., '.epub')
    """
    if target_format:
        target_format = target_format.lower().lstrip(".")
        if target_format in ["pdf", "epub", "mobi"]:
            return f".{target_format}"

    # Auto-detect based on input
    input_ext = input_path.suffix.lower()
    if input_ext == ".pdf":
        return ".epub"
    elif input_ext == ".epub":
        return ".mobi"
    elif input_ext == ".mobi":
        return ".pdf"
    else:
        return ".epub"  # Default to EPUB


def convert_ebook(
    input_file: Path, output_file: Optional[Path] = None, target_format: Optional[str] = None, **kwargs
) -> Path:
    """
    Convert ebook between supported formats.

    Args:
        input_file: Path to input file
        output_file: Optional output path. If None, auto-generates.
        target_format: Optional target format ('pdf', 'epub', 'mobi')
        **kwargs: Additional options to pass to ebook-convert

    Returns:
        Path to converted file

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If format is not supported
        subprocess.CalledProcessError: If conversion fails
    """
    # Check Calibre installation
    if not check_calibre_installed():
        raise RuntimeError(
            "Calibre is not installed. Please install it:\n"
            "  macOS: brew install calibre\n"
            "  Linux: sudo apt-get install calibre\n"
            "  Windows: Download from https://calibre-ebook.com/download"
        )

    # Validate input file
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    input_ext = input_file.suffix.lower()
    if input_ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported input format: {input_ext}\nSupported formats: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    # Generate output filename
    if output_file is None:
        output_ext = get_output_format(input_file, target_format)
        output_file = input_file.with_suffix(output_ext)

    output_ext = output_file.suffix.lower()
    if output_ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported output format: {output_ext}\n"
            f"Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    # Build command
    cmd = ["ebook-convert", str(input_file), str(output_file)]

    # Add additional options
    for key, value in kwargs.items():
        if value is True:
            cmd.append(f"--{key.replace('_', '-')}")
        elif value is not False and value is not None:
            cmd.append(f"--{key.replace('_', '-')}")
            cmd.append(str(value))

    # Run conversion
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Conversion failed: {e}") from e

    return output_file


def batch_convert(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    input_format: str = "pdf",
    output_format: str = "epub",
    **kwargs,
) -> list[Path]:
    """
    Batch convert files in a directory.

    Args:
        input_dir: Directory containing input files
        output_dir: Optional output directory (default: same as input)
        input_format: Input format extension (e.g., 'pdf', 'epub')
        output_format: Output format extension (e.g., 'epub', 'mobi')
        **kwargs: Additional options for ebook-convert

    Returns:
        List of converted file paths
    """
    input_format = input_format.lstrip(".")
    output_format = output_format.lstrip(".")

    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    input_pattern = f"*.{input_format}"
    input_files = list(input_dir.glob(input_pattern))

    if not input_files:
        print(f"No {input_format} files found in {input_dir}")
        return []

    converted_files = []
    for input_file in input_files:
        output_file = output_dir / input_file.with_suffix(f".{output_format}").name
        try:
            result = convert_ebook(input_file, output_file, **kwargs)
            converted_files.append(result)
            print(f"✅ Converted: {input_file.name} → {output_file.name}")
        except Exception as e:
            print(f"❌ Failed to convert {input_file.name}: {e}", file=sys.stderr)

    return converted_files


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert ebooks between PDF, MOBI, and EPUB formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert PDF to EPUB
  %(prog)s input.pdf output.epub

  # Convert EPUB to MOBI (auto-detect output)
  %(prog)s input.epub

  # Batch convert all PDFs to EPUB
  %(prog)s --batch --input-format pdf --output-format epub /path/to/files

  # Convert with metadata
  %(prog)s input.pdf output.epub --title "Book Title" --authors "Author"
        """,
    )

    parser.add_argument("input", nargs="?", type=Path, help="Input file path")

    parser.add_argument(
        "output", nargs="?", type=Path, help="Output file path (optional, auto-generated if not provided)"
    )

    parser.add_argument(
        "--format",
        "-f",
        dest="target_format",
        choices=["pdf", "epub", "mobi"],
        help="Target format (if output not specified)",
    )

    parser.add_argument("--batch", "-b", action="store_true", help="Batch convert files in a directory")

    parser.add_argument(
        "--input-format", default="pdf", help="Input format for batch conversion (default: pdf)"
    )

    parser.add_argument(
        "--output-format", default="epub", help="Output format for batch conversion (default: epub)"
    )

    parser.add_argument("--input-dir", type=Path, help="Input directory for batch conversion")

    parser.add_argument("--output-dir", type=Path, help="Output directory for batch conversion")

    # Common ebook-convert options
    parser.add_argument("--title", help="Book title")
    parser.add_argument("--authors", help="Book authors")
    parser.add_argument("--language", help="Book language (e.g., zh, en)")

    args = parser.parse_args()

    # Batch mode
    if args.batch or args.input_dir:
        input_dir = args.input_dir or Path.cwd()
        if not input_dir.is_dir():
            print(f"Error: {input_dir} is not a directory", file=sys.stderr)
            sys.exit(1)

        kwargs = {}
        if args.title:
            kwargs["title"] = args.title
        if args.authors:
            kwargs["authors"] = args.authors
        if args.language:
            kwargs["language"] = args.language

        batch_convert(input_dir, args.output_dir, args.input_format, args.output_format, **kwargs)
        return

    # Single file mode
    if not args.input:
        parser.print_help()
        sys.exit(1)

    kwargs = {}
    if args.title:
        kwargs["title"] = args.title
    if args.authors:
        kwargs["authors"] = args.authors
    if args.language:
        kwargs["language"] = args.language

    try:
        result = convert_ebook(args.input, args.output, args.target_format, **kwargs)
        print(f"✅ Converted: {result}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
