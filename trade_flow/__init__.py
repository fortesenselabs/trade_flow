"""
The top-level package contains all sub-packages needed for TradeFlow.
"""

from . import core
from . import adapters
from . import feed
from trade_flow.oms import orders, wallets, instruments, exchanges, services
from . import environments
from . import stochastic
from . import agents


from importlib import resources
from pathlib import Path

import toml


PACKAGE_ROOT = Path(__file__).resolve().parent.parent

try:
    __version__ = toml.load(PACKAGE_ROOT / "pyproject.toml")["tool"]["poetry"]["version"]
except FileNotFoundError:  # pragma: no cover
    __version__ = "latest"

USER_AGENT = f"TradeFlow/{__version__}"


def clean_version_string(version: str) -> str:
    """
    Clean the version string by removing any non-digit leading characters.
    """
    # Check if the version starts with any of the operators and remove them
    specifiers = ["==", ">=", "<=", "^", ">", "<"]
    for s in specifiers:
        version = version.replace(s, "")

    # Only allow digits, dots, a, b, rc characters
    return "".join(c for c in version if c.isdigit() or c in ".abrc")


def get_package_version_from_toml(
    package_name: str,
    strip_specifiers: bool = False,
) -> str:
    """
    Return the package version specified in the given `toml_file` for the given
    `package_name`.
    """
    with resources.path("your_package_name", "pyproject.toml") as toml_path:
        data = toml.load(toml_path)
        version = data["tool"]["poetry"]["dependencies"][package_name]["version"]
        if strip_specifiers:
            version = clean_version_string(version)
        return version
