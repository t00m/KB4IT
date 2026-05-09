#!/usr/bin/env python3
"""
Convert AsciiDoc files to Markdown.

Converts AsciiDoc documents to Markdown while preserving content structure.
No metadata extraction is performed - KB4IT extracts metadata from document
structure (filenames, headings) during processing.

Usage:
    python adoc_to_md_converter.py <input_dir> <output_dir> [--overwrite]
"""

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Convert AsciiDoc content to Markdown."""

    @staticmethod
    def using_pandoc(adoc_content: str) -> Optional[str]:
        """Convert AsciiDoc to Markdown using pandoc."""
        try:
            result = subprocess.run(
                ['pandoc', '-f', 'asciidoc', '-t', 'markdown'],
                input=adoc_content,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"Pandoc error: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.warning("Pandoc not found, falling back to basic conversion")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Pandoc timeout, falling back to basic conversion")
            return None

    @staticmethod
    def basic_conversion(adoc_content: str) -> str:
        """Basic AsciiDoc to Markdown conversion without pandoc."""
        content = adoc_content

        # Section headings: == Title -> ## Title, === -> ###, etc.
        content = re.sub(
            r'^(=+)\s+(.+)$',
            lambda m: '#' * len(m.group(1)) + ' ' + m.group(2),
            content,
            flags=re.MULTILINE
        )

        # Bold: *text* -> **text**
        content = re.sub(r'\*([^*\n]+)\*', r'**\1**', content)

        # Italic: _text_ -> *text*
        content = re.sub(r'_([^_\n]+)_', r'*\1*', content)

        # Monospace/code: `text` remains `text` (compatible)

        # Code blocks: [source,language] -> ```language
        content = re.sub(
            r'\[source,([^\]]+)\]\n(-{4,})',
            lambda m: f'```{m.group(1)}\n',
            content
        )
        content = re.sub(r'^(-{4,})$', '```', content, flags=re.MULTILINE)

        # Numbered lists: . item -> 1. item (basic; pandoc handles better)
        content = re.sub(r'^\. ', '1. ', content, flags=re.MULTILINE)

        # Bullet lists: * item -> - item
        content = re.sub(r'^\* ', '- ', content, flags=re.MULTILINE)

        # Nested lists: ** -> two spaces + -
        content = re.sub(r'^\*\* ', '  - ', content, flags=re.MULTILINE)

        # Links: link:url[text] -> [text](url)
        content = re.sub(r'link:([^\[]+)\[([^\]]+)\]', r'[\2](\1)', content)

        # Inline links: https://... already compatible

        # Images: image:path[alt] -> ![alt](path)
        content = re.sub(r'image:([^\[]+)\[([^\]]*)\]', r'![\2](\1)', content)

        # Admonitions: NOTE: -> (no markdown equivalent, use blockquote)
        content = re.sub(
            r'^(NOTE|TIP|IMPORTANT|WARNING|CAUTION):\s+',
            r'> **\1:** ',
            content,
            flags=re.MULTILINE
        )

        return content

    @staticmethod
    def convert(adoc_content: str) -> str:
        """Convert AsciiDoc to Markdown, trying pandoc first."""
        md = MarkdownConverter.using_pandoc(adoc_content)
        if md is not None:
            logger.debug("Used pandoc for conversion")
            return md

        logger.debug("Using basic conversion")
        return MarkdownConverter.basic_conversion(adoc_content)


def extract_title_from_content(content: str) -> Tuple[Optional[str], str]:
    """
    Extract the first heading as the title and return title + remaining content.

    Returns (title, remaining_content)
    """
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Match heading: ## Title, ### Subheading, etc.
        match = re.match(r'^(#+)\s+(.+)$', line)
        if match:
            title = match.group(2).strip()
            remaining = '\n'.join(lines[i+1:]).strip()
            return title, remaining
    return None, content


def process_file(input_file: Path, output_dir: Path, overwrite: bool = False) -> bool:
    """
    Convert a single AsciiDoc file to Markdown.

    Returns True if successful, False otherwise.
    """
    try:
        # Read AsciiDoc file
        content = input_file.read_text(encoding='utf-8')

        # Convert to Markdown
        md_content = MarkdownConverter.convert(content)

        # Extract title from first heading
        title, remaining_content = extract_title_from_content(md_content)

        if not title:
            logger.warning(f"  ⚠ No heading found in {input_file.name}, using filename as title")
            title = input_file.stem.replace('-', ' ').title()
            remaining_content = md_content

        # Create output file
        output_file = output_dir / input_file.with_suffix('.md').name

        if output_file.exists() and not overwrite:
            logger.warning(f"Skipping {output_file.name} (already exists, use --overwrite)")
            return False

        # Build output: frontmatter + title + content
        output = "---\n{}\n---\n\n"
        output += f"# {title}\n"
        if remaining_content:
            output += f"\n{remaining_content}"

        # Write output
        output_file.write_text(output, encoding='utf-8')
        logger.info(f"✓ Converted {input_file.name} → {output_file.name}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to convert {input_file.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert AsciiDoc files to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s ./docs ./docs_md
  %(prog)s ./adoc ./markdown --overwrite
        '''
    )

    parser.add_argument('input_dir', type=Path, help='Input directory with .adoc files')
    parser.add_argument('output_dir', type=Path, help='Output directory for .md files')
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing markdown files'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively process subdirectories'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate input directory
    if not args.input_dir.is_dir():
        logger.error(f"Input directory not found: {args.input_dir}")
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Find AsciiDoc files
    if args.recursive:
        adoc_files = list(args.input_dir.rglob('*.adoc'))
    else:
        adoc_files = list(args.input_dir.glob('*.adoc'))

    if not adoc_files:
        logger.warning(f"No .adoc files found in {args.input_dir}")
        return 1

    logger.info(f"Found {len(adoc_files)} AsciiDoc file(s)")

    # Process each file
    successful = 0
    for adoc_file in adoc_files:
        if process_file(adoc_file, args.output_dir, args.overwrite):
            successful += 1

    logger.info(f"\nCompleted: {successful}/{len(adoc_files)} files converted successfully")
    return 0 if successful == len(adoc_files) else 1


if __name__ == '__main__':
    sys.exit(main())
