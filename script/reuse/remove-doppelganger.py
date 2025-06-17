import re

def normalize_name(copyright_line):
    """Extrahiere den Autorennamen (ohne Jahr, E-Mail, usw.)."""
    match = re.match(r'\s*\d+\s+([^\<©]+)', copyright_line)
    return match.group(1).strip() if match else None

def clean_reuse_file(content):
    cleaned_lines = []
    in_file_block = False
    in_copyright_block = False
    current_authors = set()
    block_lines = []

    for line in content.splitlines():
        stripped = line.strip()

        if stripped == "[[File]]":
            in_file_block = True
            current_authors.clear()
            cleaned_lines.append(line)
        elif in_file_block and stripped.startswith("Copyright"):
            in_copyright_block = True
            cleaned_lines.append(line)  # z. B. "Copyright = ["
            block_lines = []
        elif in_copyright_block:
            if stripped == "]":
                # Beende Block, filtere Einträge
                seen_names = set()
                for entry in block_lines:
                    name = normalize_name(entry)
                    if name and name not in seen_names:
                        seen_names.add(name)
                        cleaned_lines.append(entry)
                cleaned_lines.append(line)  # schließende Klammer ]
                in_copyright_block = False
            else:
                block_lines.append(line)
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

# Beispielnutzung:
with open("REUSE.toml", "r", encoding="utf-8") as f:
    content = f.read()

cleaned = clean_reuse_file(content)

with open("REUSE-cleaned.toml", "w", encoding="utf-8") as f:
    f.write(cleaned)
