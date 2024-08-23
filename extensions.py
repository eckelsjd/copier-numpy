import re
import shutil
import subprocess
import unicodedata
from datetime import date
from pathlib import Path
import os

from jinja2.ext import Extension

GITHUB_SCRIPT = "https://raw.githubusercontent.com/eckelsjd/copier-numpy/main/setup_github.py"


def git_user_name(default: str) -> str:
    git = shutil.which("git")
    if not git:
        return default
    try:
        default = subprocess.check_output([git, "config", "user.name"], text=True, encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        pass
    return default


def git_user_email(default: str) -> str:
    git = shutil.which("git")
    if not git:
        return default
    try:
        default = subprocess.check_output([git, "config", "user.email"], text=True, encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        pass
    return default


def slugify(value, separator="-"):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", separator, value).strip("-_")


def format_python_version(version: str) -> str:
    """Just return the first x.x version number of a Python PEP508 version specifier"""
    first_version = version.split(",")[0]
    short_version = "3.11"
    for i, char in enumerate(first_version):
        if char.isdigit():
            short_version = first_version[i:]
            break
    version_parts = short_version.split(".")
    return (f"{'.'.join(version_parts[:2]) if len(version_parts) > 1 else version_parts[0]}"
            f"{'+' if '>' in first_version else ''}")


class TemplateDefaultExtension(Extension):
    """Provide some default answers as global variables to speed up template initialization"""
    def __init__(self, environment):
        super().__init__(environment)
        email = git_user_email('')
        print(os.getcwd())
        environment.globals["git_user_name"] = git_user_name('')
        environment.globals["git_user_email"] = email
        environment.globals["git_username"] = email.split('@')[0]
        environment.globals["github_script"] = GITHUB_SCRIPT
        environment.globals["current_year"] = date.today().year
        environment.globals["project_dir"] = Path(os.getcwd()).resolve().name
        environment.filters["slugify"] = slugify
        environment.filters["format_python_version"] = format_python_version
