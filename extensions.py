import re
import shutil
import subprocess
import unicodedata
from datetime import date
from pathlib import Path
import os
import urllib.request
import urllib

from jinja2.ext import Extension


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


def pypi_name_exists(package_name: str) -> bool:
    """Check if a package name exists in PyPI."""
    url = f'https://pypi.org/project/{package_name}'
    try:
        urllib.request.urlopen(url)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        else:
            raise


def path_exists(path: str) -> bool:
    return Path(path).exists()


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
        environment.globals["git_user_name"] = git_user_name('')
        environment.globals["git_user_email"] = email
        environment.globals["git_username"] = email.split('@')[0]
        environment.globals["current_year"] = date.today().year
        environment.globals["project_dir"] = Path(os.getcwd()).resolve().name
        environment.globals["is_copier_update"] = path_exists(".copier-answers.yml") or path_exists(".copier-answers.yaml")
        # runs *before* update/copy, so answers.yml will only exist when we are doing copier update

        environment.filters["pypi_name_exists"] = pypi_name_exists
        environment.filters["slugify"] = slugify
        environment.filters["format_python_version"] = format_python_version
