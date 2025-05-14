# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

"""
Update the scenario bundle react template:
/factsheet/templates/factsheet/index.html
"""

import glob
import os
import re

# Determine the base path of the script
script_dir = os.path.abspath(os.path.dirname(__file__))

# Paths to the static files relative to the script's directory
css_path = os.path.join(script_dir, "../factsheet/static/factsheet/css/")
js_path = os.path.join(script_dir, "../factsheet/static/factsheet/js/")

# Use glob to find the files
css_files = glob.glob(os.path.join(css_path, "main.*.css"))
js_files = glob.glob(os.path.join(js_path, "main.*.js"))

# Debugging prints to ensure we are finding the files
print("CSS Files Found:", css_files)
print("JS Files Found:", js_files)

# Check if files were found
if not css_files or not js_files:
    raise FileNotFoundError(
        "CSS or JS files not found. Please check the build output and paths."
    )

# Extract the filenames
css_filename = os.path.basename(css_files[0])
js_filename = os.path.basename(js_files[0])

# Path to your Django template relative to the script's directory
template_path = os.path.join(
    script_dir, "../factsheet/templates/factsheet/index.html"
)  # Adjust this path to your actual template

# Read the Django template
with open(template_path, "r") as file:
    template_content = file.read()

# Replace the old filenames with the new ones
template_content = re.sub(
    r"href=\"{% static 'factsheet/css/main\.[a-z0-9]+\.css' %}\"",
    f"href=\"{{% static 'factsheet/css/{css_filename}' %}}\"",
    template_content,
)

template_content = re.sub(
    r"src=\"{% static 'factsheet/js/main\.[a-z0-9]+\.js' %}\"",
    f"src=\"{{% static 'factsheet/js/{js_filename}' %}}\"",
    template_content,
)

# Write the updated content back to the template
with open(template_path, "w") as file:
    file.write(template_content)

print("Template updated successfully.")
