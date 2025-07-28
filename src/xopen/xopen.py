#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import magic
import yaml
from jsonschema import ValidationError, validate

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
    with open(config_path) as f:
        config = yaml.safe_load(f)
    with open(os.path.join(os.path.dirname(__file__), "config_schema.json")) as f:
        schema = json.load(f)
    try:
        validate(instance=config, schema=schema)
        return config
    except ValidationError as e:
        print("Invalid configuration file format:", e.message)
        exit(1)


def get_mime_type(file_path):
    if os.path.isdir(file_path):
        return "inode/directory"
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def mimetypes_matches(config_mimes: list[str], actual_mime: str) -> bool:
    return any(
        mimetype_matches(config_mime, actual_mime) for config_mime in config_mimes
    )


def mimetype_matches(config_mime: str, actual_mime: str) -> bool:
    if config_mime.endswith("/*"):
        # If configuration has a wildcard
        type = config_mime.split("/*")[0]
        return actual_mime.startswith(type)
    # No wildcard
    return config_mime == actual_mime


def filetypes_matches(config_filetypes: list[str], actual_filepath: str) -> bool:
    return any(
        filetype_matches(config_filetype, actual_filepath)
        for config_filetype in config_filetypes
    )


def filetype_matches(config_filetype: str, actual_filepath: str) -> bool:
    return actual_filepath.endswith(config_filetype)


def get_application(config, mode, mime_type, filepath) -> str | None:
    relevant_configs = (
        entry
        for entry in config
        if mode in entry["mode"]
        and (
            ("mimetypes" in entry and mimetypes_matches(entry["mimetypes"], mime_type))
            or (
                "extensions" in entry
                and filetypes_matches(entry["extensions"], filepath)
            )
        )
    )
    try:
        first_relevant_config = next(relevant_configs)
        return first_relevant_config["mode"][mode]
    except StopIteration:
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

    quoted_filepath = f"'{args.filepath}'"
    if "{}" in app:
        command = app.replace("{}", quoted_filepath)
    else:
        command = f"{app} {quoted_filepath}"

    try:
        subprocess.run(["bash", "-c", command])
    except FileNotFoundError:
        print(f"Command 'bash' not found in path {os.getenv("PATH")}")
        sys.exit(1)


if __name__ == "__main__":
    main()
