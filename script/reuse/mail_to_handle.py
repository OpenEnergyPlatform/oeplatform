# SPDX-FileCopyrightText: 2025 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later


# # import toml
# # import json
# # import re

# # # Dateien einlesen
# # with open("REUSE.toml", "r", encoding="utf-8") as f:
# #     reuse_data = toml.load(f)

# # with open("email-to-handle.json", "r", encoding="utf-8") as f:
# #     email_map = json.load(f)

# # # Autoren-Einträge durchgehen und ersetzen
# # updated_authors = {}
# # for author_entry, year in reuse_data.get("authors", {}).items():
# #     # Suche nach E-Mail im Format <email@example.com>
# #     match = re.search(r"<([^>]+)>", author_entry)
# #     if match:
# #         email = match.group(1)
# #         if email in email_map:
# #             handle = email_map[email]
# #             new_key = f"{handle}"
# #             updated_authors[new_key] = year
# #         else:
# #             # Falls kein Mapping vorhanden, Original übernehmen
# #             updated_authors[author_entry] = year
# #     else:
# #         # Kein E-Mail-Format, übernehmen
# #         updated_authors[author_entry] = year

# # # Autoren-Einträge aktualisieren
# # reuse_data["authors"] = updated_authors

# # # Neue Datei schreiben (oder überschreiben)
# # with open("REUSE.updated.toml", "w", encoding="utf-8") as f:
# #     toml.dump(reuse_data, f)

# # print("REUSE.updated.toml wurde geschrieben.")
# import os
# import json
# import re
# import toml

# # --- Lade E-Mail → GitHub-Handle Mapping ---
# with open("mail-to-github.json", "r", encoding="utf-8") as f:
#     email_map = json.load(f)

# # --- Teil 1: SPDX-Kommentare in Dateien ersetzen ---
# spdx_regex = re.compile(r"(SPDX-FileCopyrightText:\s*)(.+?)\s*<([^>]+)>")

# def process_file(path):
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             lines = f.readlines()
#     except (UnicodeDecodeError, PermissionError):
#         return False  # Nicht bearbeitbar

#     changed = False
#     new_lines = []

#     for line in lines:
#         match = spdx_regex.search(line)
#         if match:
#             prefix, name, email = match.groups()
#             if email in email_map:
#                 handle = email_map[email]
#                 new_line = f"{handle}\n"
#                 new_lines.append(new_line)
#                 changed = True
#             else:
#                 new_lines.append(line)
#         else:
#             new_lines.append(line)

#     if changed:
#         with open(path, "w", encoding="utf-8") as f:
#             f.writelines(new_lines)
#         print(f"✅ SPDX angepasst: {path}")
#         return True

#     return False

# # --- Teil 2: REUSE.toml bearbeiten ---
# def process_reuse_toml(path="REUSE.toml"):
#     if not os.path.exists(path):
#         print("⚠️ REUSE.toml nicht gefunden.")
#         return

#     reuse_data = toml.load(path)
#     updated_authors = {}
#     changed = False

#     for author_entry, year in reuse_data.get("authors", {}).items():
#         match = re.search(r"<([^>]+)>", author_entry)
#         if match:
#             email = match.group(1)
#             if email in email_map:
#                 handle = email_map[email]
#                 new_key = f"{handle}"
#                 updated_authors[new_key] = year
#                 changed = True
#             else:
#                 updated_authors[author_entry] = year
#         else:
#             updated_authors[author_entry] = year

#     if changed:
#         reuse_data["authors"] = updated_authors
#         with open(path, "w", encoding="utf-8") as f:
#             toml.dump(reuse_data, f)
#         print(f"✅ REUSE.toml aktualisiert: {path}")
#     else:
#         print("ℹ️ REUSE.toml unverändert.")

# # --- Hauptlogik: durchlaufe alle Dateien ---
# for root, dirs, files in os.walk("."):
#     for filename in files:
#         if filename in ("email_to_handle.json",):  # mapping nicht bearbeiten
#             continue
#         filepath = os.path.join(root, filename)
#         process_file(filepath)

# # --- REUSE.toml separat bearbeiten ---
# process_reuse_toml()

import os
import json
import re
import toml

# --- Lade E-Mail → GitHub-Handle Mapping ---
with open("mail-to-github.json", "r", encoding="utf-8") as f:
    email_map = json.load(f)

# Regex: Erkenne SPDX-Zeilen mit E-Mail in <...>
spdx_regex = re.compile(r"(SPDX-FileCopyrightText:\s*\d{4}\s+[^<]+<)([^>]+)(>)")

def process_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        return False  # Nicht bearbeitbar

    changed = False
    new_lines = []

    for line in lines:
        match = spdx_regex.search(line)
        if match:
            start, email, end = match.groups()
            if email in email_map:
                handle = f"{email_map[email]}"
                new_line = spdx_regex.sub(f"\\1{handle}\\3", line)
                new_lines.append(new_line)
                changed = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ SPDX-Mail ersetzt: {path}")
        return True

    return False

# --- REUSE.toml anpassen ---
# def process_reuse_toml(path="REUSE.toml"):
#     if not os.path.exists(path):
#         print("⚠️ REUSE.toml nicht gefunden.")
#         return

#     reuse_data = toml.load(path)
#     updated_authors = {}
#     changed = False

#     for author_entry, year in reuse_data.get("authors", {}).items():
#         match = re.search(r"<([^>]+)>", author_entry)
#         if match:
#             email = match.group(1)
#             if email in email_map:
#                 handle = email_map[email]
#                 new_key = re.sub(r"<[^>]+>", f"<{handle}>", author_entry)
#                 updated_authors[new_key] = year
#                 changed = True
#             else:
#                 updated_authors[author_entry] = year
#         else:
#             updated_authors[author_entry] = year

#     if changed:
#         reuse_data["authors"] = updated_authors
#         with open(path, "w", encoding="utf-8") as f:
#             toml.dump(reuse_data, f)
#         print(f"✅ REUSE.toml aktualisiert.")
#     else:
#         print("ℹ️ REUSE.toml unverändert.")

def process_reuse_toml(path="REUSE.toml"):
    if not os.path.exists(path):
        print("⚠️ REUSE.toml nicht gefunden.")
        return

    changed = False
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Nur Zeilen mit <email> ersetzen
            match = re.search(r"<([^>]+)>", line)
            if match:
                email = match.group(1)
                if email in email_map:
                    handle = f"{email_map[email]}"
                    newline = re.sub(r"<[^>]+>", f"<{handle}>", line)
                    lines.append(newline)
                    changed = True
                    continue
            lines.append(line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ REUSE.toml angepasst.")
    else:
        print("ℹ️ REUSE.toml unverändert.")

# --- Alle Dateien im Repo durchgehen ---
for root, dirs, files in os.walk("."):
    for filename in files:
        if filename in ("mail-to-github.json",):
            continue
        filepath = os.path.join(root, filename)
        process_file(filepath)

# --- REUSE.toml separat anpassen ---
process_reuse_toml()
