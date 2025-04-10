import os
import subprocess
from reuse import Project
from reuse.files import File

# License mappings
LICENSE_MAP = {
    "code": "MIT",
    "docs": "CC0-1.0",
    "media": "CC-BY-4.0",
}

# Your name/email
COPYRIGHT = "2024 Your Name <your@email.com>"

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
        # Default to MIT for unknown files, but mark as non-commentable
        return LICENSE_MAP["code"], False

def main():
    project = Project(os.getcwd())

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

            if commentable:
                try:
                    subprocess.run([
                        "reuse", "addheader",
                        "--copyright", COPYRIGHT,
                        "--license", license_id,
                        rel_path
                    ], check=True)
                    print(f"Header added to {rel_path} with {license_id}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to add header to {rel_path}: {e}")
            else:
                # Add to .reuse/dep5
                file_obj = File(rel_path, project)
                file_obj.mark_license(license_id)
                file_obj.mark_copyright(COPYRIGHT)
                file_obj.dump()
                print(f"Marked {rel_path} in .reuse/dep5 with {license_id}")

if __name__ == "__main__":
    main()
