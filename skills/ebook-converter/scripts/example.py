#!/usr/bin/env python3
"""
Example script for ebook-converter.
Batch converts PDF/EPUB files to MOBI format.
"""

import subprocess
import sys
from pathlib import Path


def convert_to_mobi(input_file: Path, output_dir: Path = None):
    """
    Convert a PDF or EPUB file to MOBI format.

    Args:
        input_file: Path to input file (PDF or EPUB)
        output_dir: Output directory (default: same as input file)

    Returns:
        Path to output file if successful, None otherwise
    """
    if output_dir is None:
        output_dir = input_file.parent

    output_file = output_dir / f"{input_file.stem}.mobi"

    # Check if output already exists
    if output_file.exists():
        print(f"⚠️  Output file already exists: {output_file}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Skipped.")
            return None

    try:
        print(f"Converting: {input_file.name} → {output_file.name}")
        subprocess.run(
            ["ebook-converter", str(input_file), str(output_file)], check=True, capture_output=True
        )
        print(f"✅ Successfully converted: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Conversion failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Error details: {e.stderr.decode()}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("❌ Error: ebook-converter not found. Make sure it's installed.", file=sys.stderr)
        return None


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python example.py <input_file> [output_dir]")
        print("Example: python example.py book.pdf")
        print("Example: python example.py book.epub ./output")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() not in [".pdf", ".epub"]:
        print(f"⚠️  Warning: {input_path.suffix} may not be supported", file=sys.stderr)
        print("Supported formats: .pdf, .epub")

    result = convert_to_mobi(input_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
