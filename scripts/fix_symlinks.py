"""Fix VERSION symlinks that aren't resolved on Windows.

On Windows without Developer Mode, git checks out symlinks as plain text
files containing the target path. This script detects those and replaces
them with the actual target content.

Usage: python scripts/fix_symlinks.py
"""

import os
import subprocess

# Only fix these files — they break the Python build.
TARGETS = [
    "python/librmm/librmm/VERSION",
    "python/rmm/rmm/VERSION",
]


def main():
    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()

    fixed = 0
    for filepath in TARGETS:
        full_path = os.path.join(repo_root, filepath)
        if not os.path.isfile(full_path):
            continue

        content = open(full_path, "r").read().strip()
        if "/" not in content and "\\" not in content:
            continue

        target = os.path.normpath(
            os.path.join(os.path.dirname(full_path), content)
        )
        if os.path.isfile(target):
            target_content = open(target, "r").read()
            with open(full_path, "w") as f:
                f.write(target_content)
            print(f"Fixed: {filepath} -> {content}")
            fixed += 1
        else:
            print(f"Warning: {filepath} -> {content} (target not found: {target})")

    if fixed:
        print(f"\nFixed {fixed} symlink(s).")
    else:
        print("No broken symlinks found (symlinks are working or already fixed).")


if __name__ == "__main__":
    main()
