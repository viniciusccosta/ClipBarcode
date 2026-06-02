import subprocess
import tempfile

import toml
from packaging import version

try:
    # Load PR branch version
    with open("pyproject.toml", "r") as f:
        pr_version = toml.load(f)["tool"]["poetry"]["version"]

    # Get pyproject.toml from main branch
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml") as tmp:
        subprocess.run(
            ["git", "show", "origin/master:pyproject.toml"],
            stdout=tmp,
            text=True,
            check=True,
        )
        tmp.seek(0)
        main_version = toml.load(tmp)["tool"]["poetry"]["version"]

    # Compare versions
    if version.parse(pr_version) <= version.parse(main_version):
        print(f"Error: Version {pr_version} is not greater than {main_version}")
        exit(1)

    print(f"Version bump valid: {main_version} -> {pr_version}")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
