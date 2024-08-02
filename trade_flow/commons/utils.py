import os
import stat
from pathlib import Path
import subprocess
from trade_flow.commons.logging import Logger

logger = Logger(name="utils")

def get_architecture():
    """
    Get the architecture of the machine.
    :return: The architecture of the machine or None if an error occurred
    """
    result = subprocess.run(["uname", "-m"], stdout=subprocess.PIPE)
    arch = result.stdout.decode("utf-8").strip()
    if arch == "x86_64":
        arch = "amd64"
    if arch is None:
        raise Exception("Failed to detect architecture.")
    return arch

def gen_config_dir(flow_name: str) -> Path:
    """
    Determine a config dir based on flow name
    """
    config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.trade_flow"))
    config_dir = Path(config_dir) / "trade_flow" / flow_name
    return config_dir


def remove_version_prefix(version_str):
    if version_str.startswith("0."):
        return version_str[2:]
    return version_str


def set_execute_permission(file_path):
    current_permissions = os.stat(file_path).st_mode
    os.chmod(file_path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
