#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

import magic
import yaml

# TODO run black and ruff with poetry
# TODO write automated tests
# TODO create a bash wrapper. Does Poetry have something to suppor this going in /bin?
# TODO ensure proper wildcard support
# TODO make a fallback category?

CONFIG_PATHS = [
    os.getenv("XOPEN_CONFIG"),
    # TODO add support for the XDG config dirs and friends: https://specifications.freedesktop.org/basedir-spec/latest/
    Path.home() / ".config" / "xopen" / "config.yml",
]


def load_config():
    available_config_paths = [
        path for path in CONFIG_PATHS if path and os.path.exists(path)
    ]
    try:
        config_path = available_config_paths[0]
    except IndexError:
        print("Configuration file not found.")
        sys.exit(1)
    with open(config_path) as file:
        return yaml.safe_load(file)


def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def get_application(config, mode, mime_type, filepath):
    print(config)
    print(mime_type)
    print(mode)
    relevant_configs = (
        entry
        for entry in config
        if mode in entry["mode"]
        and (
            ("mime" in entry and mime_type == entry["mime"])
            or ("extension" in entry and filepath.endswith(entry["extension"]))
        )
    )
    first_relevant_config = next(relevant_configs)
    if first_relevant_config:
        return first_relevant_config["mode"][mode]

    return None


def main():
    # TODO support opening multiple files through multiple arguments
    parser = argparse.ArgumentParser(description="Open a file with the desired mode.")
    parser.add_argument("mode", help="Mode of open: 'view' or 'edit'")
    parser.add_argument("filepath", help="Path of the file to open")

    args = parser.parse_args()
    config = load_config()
    mime_type = get_mime_type(args.filepath)
    app = get_application(config, args.mode, mime_type, args.filepath)

    if not app:
        # TODO support fallback
        print(
            f"No application configured for mode '{args.mode}' for file '{args.filepath}'"
        )
        sys.exit(1)

    try:
        subprocess.run([app, args.filepath])
    except FileNotFoundError:
        print(f"Command '{app}' not found in path {os.getenv("PATH")}")
        sys.exit(1)


if __name__ == "__main__":
    main()
