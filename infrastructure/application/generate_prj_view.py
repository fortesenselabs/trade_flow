"""This module provides functionality to generate and print directory tree structure."""

from __future__ import annotations

import os


def generate_project_tree(directory: str, indent: str = "", last: bool = True) -> None:
    """
    Recursively generates and prints the directory tree structure starting from the given directory.

    Args:
        directory: The path to the directory whose tree structure is to be generated.
        indent: The indentation string to be used for formatting tree levels.
        last: Flag indicating whether the current directory is the last item at its level in the tree.

    Returns:
        None
    """
    print(indent, end="")
    if last:
        print("└──", end="")
        new_indent = indent + "    "
    else:
        print("├──", end="")
        new_indent = indent + "│   "
    print(os.path.basename(directory) + "/")
    items = os.listdir(directory)
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            generate_project_tree(item_path, new_indent, is_last)


def main() -> None:
    directory_path = "."
    generate_project_tree(directory_path)


if __name__ == "__main__":
    main()
