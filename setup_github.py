import subprocess
import platform
import shlex
from pathlib import Path
import re


def run_command(command):
    try:
        result = subprocess.run(shlex.split(command), capture_output=True, check=True)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}") from e


def install_gh_cli():
    """Installs GitHub CLI (gh) based on the operating system."""
    try:
        run_command("gh --version")
        print("GitHub CLI is already installed.")
    except RuntimeError:
        print("Installing GitHub CLI...")
        os_type = platform.system().lower()

        if os_type == "linux":
            print('Attempt Linux install of GitHub CLI...')
            distro = platform.linux_distribution()[0].lower()
            if "ubuntu" in distro or "debian" in distro:
                run_command("(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y))")
                run_command("sudo mkdir -p -m 755 /etc/apt/keyrings")
                run_command("wget -q0- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null")
                run_command("sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg")
                run_command('echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null')
                run_command("sudo apt update")
                run_command("sudo apt install gh -y")
            elif "fedora" in distro or "centos" in distro or "rhel" in distro:
                run_command("sudo dnf install 'dnf-command(config-manager)' -y")
                run_command("sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo")
                run_command("sudo dnf install gh --repo gh-cli -y")
            else:
                raise NotImplementedError(f"Unsupported Linux distribution: {distro}")
        elif os_type == "darwin":
            print('Attempt MacOS install of Github CLI...')
            try:
                run_command("brew --version")
            except RuntimeError:
                run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            run_command("brew install gh")
        elif os_type == 'windows':
            print('Attempt Windows install of Github CLI...')
            try:
                run_command("scoop --version")
            except RuntimeError:
                run_command('powershell -command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"')
                run_command('powershell -command "Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"')
            run_command("scoop install gh")
        else:
            raise NotImplementedError(f"Unsupported operating system: {os_type}")

        print("GitHub CLI installed successfully.")


def authenticate_gh():
    """Authenticates gh CLI."""
    try:
        print("Setting up GitHub authentication...")
        run_command("gh auth login")
    except RuntimeError as e:
        print(f"Authentication failed: {e}")


def parse_pyproject_toml(keys):
    result = {"description": "Description of your repository", "license": "MIT"}
    keys_to_search = keys.copy()
    try:
        with open("pyproject.toml", "r") as fd:
            for line in fd.readlines():
                if len(keys_to_search) > 0:
                    for key in keys:
                        if key in keys_to_search and f"{key} = " in line:
                            result[key] = re.findall('"([^"]*)"', line)[0]
                            keys_to_search.remove(key)
    except FileNotFoundError:
        print('Could not find pyproject.toml!')
    finally:
        return result


def initialize_git_repo():
    """Initializes git repository and sets up GitHub repository."""
    try:
        if Path('.git').exists():
            print(f'A git repo already exists in the current directory!')
        else:
            print("Initializing Git repository...")
            run_command("git config --global init.defaultBranch main")
            run_command("git init")
            run_command("git add .")
            run_command('git commit -m "init: initial commit from copier-numpy"')
        try:
            run_command("gh repo view")
            print("GitHub repo is already initialized!")
        except RuntimeError:
            print("Creating GitHub repository and pushing code...")
            pyproj_values = parse_pyproject_toml(["description", "license"])
            run_command(f'gh repo create --public --source=. --remote=origin --disable-wiki '
                        f'--description="{pyproj_values["description"]}", --license="{pyproj_values["license"]}"')
            run_command("git push -u origin main")

    except RuntimeError as e:
        print(f"Git setup failed: {e}")


def initialize_git_repo_settings():
    """Use all the good defaults for the GitHub repository."""
    if Path(".github/workflows/docs.yml").exists():
        run_command('gh api -X POST /repos/{owner}/{repo}/pages -f source="branch:gh-pages"')

    run_command('gh repo edit {owner}/{repo} --add-topic pdm --add-topic python --add-topic copier-template '
                '--add-topic numpy --delete-branch-on-merge --enable-discussions --enable-issues '
                '--enable-wiki=false --enable-projects=false --enable-merge-commit=false --enable-rebase-merge '
                '--enable-squash-merge --visibility public --allow-update-branch')

    # Setup main and v* ruleset protections
    gh_cmd = 'gh api --method POST -H "Accept: application/vnd.github+json" /repos/{owner}/{repo}/rulesets --input'
    for rule_name in ['main', 'vtag']:
        rule_file = f"https://raw.githubusercontent.com/eckelsjd/copier-numpy/main/.github/protect-{rule_name}.json"
        if platform.system().lower().startswith('win'):
            run_command(f'powershell -command "(Invoke-WebRequest -Uri {rule_file} -UseBasicParsing).Content" | {gh_cmd} -')
        else:
            run_command(f"curl -sSL {rule_file} | {gh_cmd} -")


def initialize_pre_commit():
    if Path(".pre-commit-config.yaml").exists():
        print("Initializing pre-commit config...")
        run_command("pdm run pre-commit install")


if __name__ == "__main__":
    install_gh_cli()
    authenticate_gh()
    initialize_git_repo()
    initialize_git_repo_settings()
    initialize_pre_commit()
