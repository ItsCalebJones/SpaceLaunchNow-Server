#!/usr/bin/env python3
"""
Parse poetry show text output to detect package updates.
Usage: python parse-package-updates.py before-all-packages.txt after-update.txt before-update.txt
"""

import re
import sys
from pathlib import Path


def parse_poetry_show_output(filepath):
    """Parse poetry show output and extract package name/version pairs."""
    packages = {}
    try:
        if not Path(filepath).exists():
            return packages

        with open(filepath) as f:
            for line in f:
                line = line.strip()
                # Poetry show format: "package-name (version) description"
                match = re.match(r"^([a-zA-Z0-9_-]+)\s+\(([^)]+)\)", line)
                if match:
                    name, version = match.groups()
                    packages[name] = version
    except (OSError, FileNotFoundError):
        pass

    return packages


def parse_outdated_packages(filepath):
    """Parse poetry show --outdated output to get available updates."""
    outdated = {}
    try:
        if not Path(filepath).exists():
            return outdated

        with open(filepath) as f:
            for line in f:
                line = line.strip()
                # Outdated format: "package-name (current) (latest) description"
                match = re.match(r"^([a-zA-Z0-9_-]+)\s+\(([^)]+)\)\s+\(([^)]+)\)", line)
                if match:
                    name, current, latest = match.groups()
                    outdated[name] = {"current": current, "latest": latest}
    except (OSError, FileNotFoundError):
        pass

    return outdated


def main():
    if len(sys.argv) != 4:
        print("Usage: python parse-package-updates.py before-all-packages.txt after-update.txt before-update.txt")
        sys.exit(1)

    before_all_file, after_file, before_outdated_file = sys.argv[1], sys.argv[2], sys.argv[3]

    # Load package data
    before_packages = parse_poetry_show_output(before_all_file)
    after_packages = parse_poetry_show_output(after_file)
    before_outdated = parse_outdated_packages(before_outdated_file)

    updates = []
    new_packages = []
    removed_packages = []

    # Find updated packages
    for name, new_version in after_packages.items():
        if name in before_packages:
            old_version = before_packages[name]
            if old_version != new_version:
                updates.append(f"- **{name}**: {old_version} → {new_version}")
        else:
            new_packages.append(f"- **{name}**: {new_version} (new)")

    # Find removed packages
    for name, old_version in before_packages.items():
        if name not in after_packages:
            removed_packages.append(f"- **{name}**: {old_version} (removed)")

    # Output results
    print("### Updated Packages:")

    if updates:
        print("\n#### Package Updates:")
        for update in updates[:15]:  # Limit to avoid overwhelming output
            print(update)
        if len(updates) > 15:
            print(f"- ... and {len(updates) - 15} more package updates")

    if new_packages:
        print("\n#### New Packages:")
        for pkg in new_packages[:10]:
            print(pkg)
        if len(new_packages) > 10:
            print(f"- ... and {len(new_packages) - 10} more new packages")

    if removed_packages:
        print("\n#### Removed Packages:")
        for pkg in removed_packages:
            print(pkg)

    if not updates and not new_packages and not removed_packages:
        total_packages = len(after_packages)
        outdated_count = len(before_outdated)
        if total_packages > 0:
            print(f"- {total_packages} packages checked for updates")
            if outdated_count > 0:
                print(f"- {outdated_count} packages were outdated before update")
            print("- Poetry lock file updated (dependency resolution changes)")
        else:
            print("- Package metadata or constraints updated")


if __name__ == "__main__":
    main()
