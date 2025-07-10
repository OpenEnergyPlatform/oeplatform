# SPDX-FileCopyrightText: 2025 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import toml
from pathlib import Path

# def parse_dep5(dep5_path):
#     with open(dep5_path, "r", encoding="utf-8") as f:
#         lines = f.readlines()

#     entries = []
#     current = {}
#     current_copyright = []

#     for line in lines:
#         line = line.rstrip("\n")
#         if not line.strip():
#             if current:
#                 # Save current block
#                 if current:
#                     current["Copyright"] = current_copyright
#                     entries.append(current)
#                 current = {}
#                 current_copyright = []
#             continue

#         if line.startswith("Files:"):
#             current["Files"] = [f.strip() for f in line[len("Files:"):].strip().split()]
#         elif line.startswith("License:"):
#             current["License"] = line[len("License:"):].strip()
#         elif line.startswith("Copyright:"):
#             current_copyright.append(line[len("Copyright:"):].strip())
#         else:
#             # Support for continued lines (indented lines)
#             if line.startswith(" "):
#                 if "License" in current and not current_copyright:
#                     current["License"] += " " + line.strip()
#                 elif current_copyright:
#                     current_copyright[-1] += " " + line.strip()

#     if current:
#         current["Copyright"] = current_copyright
#         entries.append(current)

#     return entries

def parse_dep5(dep5_path):
    with open(dep5_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    current = {}
    current_copyright = []

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            if current:
                current["Copyright"] = current_copyright
                entries.append(current)
                current = {}
                current_copyright = []
            continue

        if line.startswith("Files:"):
            current["Files"] = [f.strip() for f in line[len("Files:"):].strip().split()]
        elif line.startswith("License:"):
            current["License"] = line[len("License:"):].strip()
        elif line.startswith("Copyright:"):
            current_copyright.append(line[len("Copyright:"):].strip())
        elif line.startswith(" "):
            stripped = line.strip()
            if "License" in current and not current_copyright:
                current["License"] += " " + stripped
            elif current_copyright is not None:
                current_copyright.append(stripped)

    if current:
        current["Copyright"] = current_copyright
        entries.append(current)

    return entries


def build_reuse_toml(entries):
    reuse_entries = []

    for entry in entries:
        license_name = entry.get("License", "NO-LICENSE").strip()
        for file_path in entry["Files"]:
            reuse_entries.append({
                "Path": file_path,
                "Licenses": [license_name],
                "Copyright": entry.get("Copyright", [])
            })
    return {"File": reuse_entries}

# def build_reuse_toml(entries):
#     reuse_entries = []

#     for entry in entries:
#         license_name = entry.get("License", "NO-LICENSE").strip()
#         copyrights = entry.get("Copyright", [])
#         for file_path in entry["Files"]:
#             reuse_entries.append({
#                 "Path": file_path,
#                 "Licenses": [license_name],
#                 "Copyright": copyrights  # <- hier wird jetzt die ganze Liste übernommen
#             })
#     return {"File": reuse_entries}

def main():
    dep5_file = ".reuse/dep5"  # oder z. B. "debian/copyright"
    output_file = "REUSE.toml"

    entries = parse_dep5(dep5_file)
    reuse_data = build_reuse_toml(entries)

    with open(output_file, "w", encoding="utf-8") as f:
        toml.dump(reuse_data, f)

    print(f"✅ REUSE.toml erstellt mit {len(reuse_data['File'])} Einträgen.")

if __name__ == "__main__":
    main()
