# SPDX-FileCopyrightText: 2025 vismayajochem <vismayajochem>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import subprocess

# License mapping
LICENSE_MAP = {
    "code": "MIT",
    "docs": "CC0-1.0",
    "media": "CC-BY-4.0",
}

# File groups
COMMENTABLE_CODE = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".sh", ".go", ".rs"}
COMMENTABLE_DOCS = {".md", ".txt", ".rst"}
UNCOMMENTABLE_MEDIA = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".tiff"}

def get_license_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in COMMENTABLE_CODE:
        return LICENSE_MAP["code"], True
    elif ext in COMMENTABLE_DOCS:
        return LICENSE_MAP["docs"], True
    elif ext in UNCOMMENTABLE_MEDIA:
        return LICENSE_MAP["media"], False
    else:
        return LICENSE_MAP["code"], False

def get_git_authors(filepath):
    try:
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%an <%ae>", "--", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        authors_raw = result.stdout.strip().split("\n")
        seen = set()
        authors = []
        for line in authors_raw:
            if line and line not in seen:
                seen.add(line)
                authors.append(line)
        return authors
    except subprocess.CalledProcessError:
        return []

def add_to_dep5(filepath, authors, license_id):
    dep5_block = f"\nFiles: {filepath}\n"
    for author in authors:
        dep5_block += f"Copyright: {author}\n"
    dep5_block += f"License: {license_id}\n"
    
    with open(".reuse/dep5", "a", encoding="utf-8") as f:
        f.write(dep5_block)

def main():
    for root, _, files in os.walk("."):
        if root.startswith("./.reuse") or ".git" in root:
            continue

        for filename in files:
            filepath = os.path.join(root, filename)
            if not os.path.isfile(filepath):
                continue
            if "LICENSES" in filepath:
                continue

            rel_path = os.path.relpath(filepath, os.getcwd())
            license_id, commentable = get_license_type(filename)
            authors = get_git_authors(rel_path)

            if not authors:
                print(f"⚠️  No authors found for {rel_path}, skipping.")
                continue

            if commentable:
                try:
                    subprocess.run([
                        "reuse", "addheader",
                        *(f"--copyright={a}" for a in authors),
                        f"--license={license_id}",
                        rel_path
                    ], check=True)
                    print(f"✅ Header added to {rel_path} with {license_id}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to add header to {rel_path}: {e}")
            else:
                add_to_dep5(rel_path, authors, license_id)
                print(f"📄 Added {rel_path} to .reuse/dep5 with {license_id}")

if __name__ == "__main__":
    main()
