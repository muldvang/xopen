#!/usr/bin/env python3

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path

import magic

# TODO run black and ruff with poetry
# TODO write automated tests
# TODO ensure proper wildcard support
# TODO make a fallback category?

CONFIG_PATHS = [
    os.getenv("XOPEN_CONFIG"),
    # TODO add support for the XDG config dirs and friends: https://specifications.freedesktop.org/basedir-spec/latest/
    Path.home() / ".config" / "xopen" / "config.ini"
]


def load_config():
    available_config_paths = [path for path in CONFIG_PATHS if path and os.path.exists(path)]
    try:
        config_path = available_config_paths[0]
    except IndexError:
        print("Configuration file not found.")
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def get_application(config, mode, mime_type):
    if config.has_option(mode, mime_type):
        return config.get(mode, mime_type)

    main_type = mime_type.split('/')[0]
    wildcard_key = f"{main_type}/*"
    if config.has_option(mode, wildcard_key):
        return config.get(mode, wildcard_key)

    return None


def main():
    # TODO support opening multiple files through multiple arguments
    parser = argparse.ArgumentParser(description="Open a file with the desired mode.")
    parser.add_argument( "mode",
        help="Mode of open: 'view' or 'edit'"
    )
    parser.add_argument( "filepath",
        help="Path of the file to open"
    )

    args = parser.parse_args()
    config = load_config()
    mime_type = get_mime_type(args.filepath)
    app = get_application(config, args.mode, mime_type)

    if not app:
        # TODO support fallback
        print(f"No application configured for mode '{args.mode}' and MIME type '{mime_type}'")
        sys.exit(1)

    try:
        subprocess.run([app, args.filepath])
    except FileNotFoundError:
        print(f"Command '{app}' not found in path {os.getenv("PATH")}")
        sys.exit(1)


if __name__ == "__main__":
    main()
