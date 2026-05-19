import os
import re
import glob
from pathlib import Path
import pydowndoc


"""
Convert previous KB4IT documents
From: Asciidoc 
To: Markdown with YAML Frontmatter
"""

def parse_asciidoc_header(content):
    """
    Extract Asciidoc header attributes and return as dictionary.
    Format:
    First line: = Title
    Then attribute lines: :Key: value
    Then end marker: // END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE
    """
    lines = content.split('\n')
    
    header_data = {}
    title = None
    header_lines = []
    
    # Find the title (first line should start with '= ')
    if lines and lines[0].startswith('= '):
        title = lines[0][2:].strip()  # Remove '= ' prefix
        header_lines.append(lines[0])
    else:
        # No title found
        return None, None, []

    # Parse header lines until END-OF-HEADER marker
    header_start = 1  # Start after title
    header_end_line = None
    
    for i in range(header_start, len(lines)):
        line = lines[i]
        
        # Check for END-OF-HEADER marker
        if '// END-OF-HEADER' in line:
            header_end_line = i + 1  # Include the marker line
            header_lines.append(line)
            break
        
        # Check for Asciidoc attribute line
        if re.match(r'^:[A-Za-z][A-Za-z0-9_-]*:', line):
            match = re.match(r'^:([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$', line)
            if match:
                key, value = match.groups()
                header_data[key] = value.strip()
            header_lines.append(line)
        else:
            # If we encounter a line that's not an attribute and not the marker,
            # we've reached the end of the header
            header_end_line = i
            continue
    
    # If we never found the END-OF-HEADER marker, assume header ends at first blank line
    if header_end_line is None:
        for i in range(header_start, len(lines)):
            if lines[i].strip() == '':
                header_end_line = i
                break
        else:
            header_end_line = len(lines)
    
    return title, header_data, header_lines, header_end_line


def convert_to_frontmatter(header_data):
    """
    Convert header dictionary to YAML Frontmatter format.
    """
    frontmatter = ['---']
    
    # Preserve order (optional - you can sort keys if needed)
    for key, value in header_data.items():
        frontmatter.append(f"{key}: {value}")
    
    frontmatter.append('---')
    return '\n'.join(frontmatter)


adoc_files = glob.glob('*.adoc')
for source in adoc_files:
    print(f"Current source: {source}")
    content = open(source).read()
    title, header_data, header_lines, header_end_line = parse_asciidoc_header(content)
    frontmatter = convert_to_frontmatter(header_data) 
    tmpfile = source.replace('.adoc', '.tmp')
    target = source.replace('.adoc', '.md')
    pydowndoc.convert_file(Path(source), output_location=Path(tmpfile))
    content = open(tmpfile).read()
    with open(target, 'w') as fmd:
      fmd.write(frontmatter)
      fmd.write("\n\n")
      fmd.write(content)
    os.unlink(tmpfile) 
    print(f"{source} converted to KB4IT document {target}")      

