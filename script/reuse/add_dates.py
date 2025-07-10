# SPDX-FileCopyrightText: 2025 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess
import re
from pathlib import Path

REUSE_FILE = "REUSE.toml"

def get_author_years(file_path):
    """Ermittelt für jede*n Autor*in das erste Jahr der Bearbeitung einer Datei."""
    git_command = [
        "git", "log", "--reverse",
        "--format=%an <%ae> %ad", "--date=short", "--", file_path
    ]
    result = subprocess.run(git_command, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")

    author_year_map = {}
    for line in lines:
        try:
            parts = line.rsplit(" ", 1)
            author_email = parts[0].strip()
            date = parts[1]
            year = date.split("-")[0]
            if author_email not in author_year_map:
                author_year_map[author_email] = year
        except IndexError:
            continue

    return author_year_map


def update_reuse_file():
    content = Path(REUSE_FILE).read_text(encoding="utf-8")

    updated_blocks = []
    file_blocks = re.findall(r'(?s)(\[\[File\]\]\s*Path = "[^"]+"\s*Licenses = \[[^\]]*\]\s*Copyright = \[[^\]]*\])', content)

    for block in file_blocks:
        path_match = re.search(r'Path = "([^"]+)"', block)
        if not path_match:
            updated_blocks.append(block)
            continue

        file_path = path_match.group(1)
        author_years = get_author_years(file_path)

        # Ersetze alte Copyright-Zeile
        old_copyright = re.findall(r'"([^"]+ <[^"]+>)"', block)
        new_lines = []
        for entry in old_copyright:
            year = author_years.get(entry)
            if year:
                new_lines.append(f'  "{year} {entry}",')
            else:
                # Kein Jahr gefunden → Eintrag beibehalten
                new_lines.append(f'  "{entry}",')

        new_block = re.sub(
            r'Copyright = \[[^\]]*\]',
            'Copyright = [\n' + "\n".join(new_lines) + '\n]',
            block
        )
        updated_blocks.append(new_block)

    # Ersetze alle alten Blöcke im Inhalt
    for old, new in zip(file_blocks, updated_blocks):
        content = content.replace(old, new)

    Path(REUSE_FILE).write_text(content, encoding="utf-8")
    print("REUSE.toml wurde erfolgreich aktualisiert.")

if __name__ == "__main__":
    update_reuse_file()


# import subprocess

# # Pfad zur Datei, für die die Copyright-Informationen generiert werden sollen
# file_path = "base/static/css/index-style.css"

# # Git-Befehl: zeigt erste Commit-Daten jedes Autors an der Datei
# git_command = [
#     "git", "log", "--reverse",
#     "--format=%an <%ae> %ad",
#     "--date=short", "--", file_path
# ]

# # Führe den Befehl aus und hole den Output
# result = subprocess.run(git_command, capture_output=True, text=True, check=True)
# lines = result.stdout.strip().split('\n')

# # Map für früheste Einträge pro Autor+E-Mail
# author_year_map = {}

# for line in lines:
#     try:
#         parts = line.rsplit(" ", 1)
#         author_email = parts[0]
#         date = parts[1]
#         year = date.split("-")[0]

#         if author_email not in author_year_map:
#             author_year_map[author_email] = year
#     except IndexError:
#         continue

# # Ausgabe in REUSE.toml-Format
# print('[[File]]')
# print(f'Path = "{file_path}"')
# print('Licenses = [ "MIT",]')
# print('Copyright = [')

# # Sortiert nach Jahr und Name
# for author_email, year in sorted(author_year_map.items(), key=lambda x: (x[1], x[0])):
#     print(f'  "{year} {author_email}",')

# print(']')
