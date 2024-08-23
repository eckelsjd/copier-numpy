"""This script will:

1) Install Github CLI (if needed)
2) Authenticate github
3) Create a license file
4) Start a local git repo and push to Github (if needed)
5) Give the Github remote repo some nice settings
6) Initialize pre-commit hooks in the local repo

TODO (catch possible failures and give useful output messages):
- Any problems installing gh CLI (and safely exit)
- Options to detect and change who is logged in to gh CLI (or exit)
- If license file couldn't be retrieved (but safely continue)
- If local repo already exists (can still continue)
- If remote repo already exists (can still continue)
- If gh-pages already exists (can still continue)
- If gh descriptions update fail for some reason (can still continue)

!!! Note "Powershell commands"
    The trick with powershell string parsing is to run subprocess(shlex.split(ps_str), shell=False),
    where ps_str = f"powershell -command '{inner_cmd}'", and inner_cmd can use double quotes for holding strings
    with spaces together, e.g. inner_cmd = f'run command --description="My description here"'.

    The way this works:
    1) shlex.split will give ['powershell', '-command', 'inner_cmd']
    2) This will always run `inner_cmd` from powershell (not cmd.exe), therefore powershell string format rules apply
    3) `inner_cmd` can now contain items like "Hello there" with double quotes as if it were running directly in ps

!!! Note "Unallowed rules"
    The following ruleset rules for branch/tag protection are not supported under free Github:
        {
          "type": "tag_name_pattern",
          "parameters": {
            "operator": "regex",
            "pattern": "^v\\d+\\.\\d+\\.\\d+((a|b|rc)\\d*|-(a|b|rc)\\d*)?"
          }
        },
        {
          "type": "commit_message_pattern",
          "parameters": {
            "name": "",
            "negate": false,
            "pattern": "^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\\([\\w\\-\\.]+\\))?(!)?: ([\\w ])+([\\s\\S]*)",
            "operator": "regex"
          }
        }
"""
import subprocess
import platform
import tempfile
from pathlib import Path
import re
import os
import getpass
import json
import sys


PLATFORM = platform.system().lower()


def run_command(command, capture_output=True, text=None):
    try:
        if PLATFORM == 'windows':
            command = ['powershell', '-command', command]
        return subprocess.run(command, capture_output=capture_output, check=True, text=text)
    except Exception as e:
        raise RuntimeError(f"Command '{command}' returned non-zero exit status.") from e


def install_gh_cli():
    """Installs GitHub CLI (gh) based on the operating system."""
    try:
        run_command("gh --version")
        print("> GitHub CLI is already installed.")
    except RuntimeError:
        print("> Installing GitHub CLI...")
        if PLATFORM == "linux":
            print('> Attempt Linux install of GitHub CLI...')
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
        elif PLATFORM == "darwin":
            print('> Attempt MacOS install of Github CLI...')
            try:
                run_command("brew --version")
            except RuntimeError:
                run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            run_command("brew install gh")
        elif PLATFORM == 'windows':
            print('> Attempt Windows install of Github CLI...')
            try:
                run_command(f'scoop --version')
            except RuntimeError:
                run_command('Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser')
                run_command('Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression')
                os.environ['PATH'] += (f"{os.pathsep if os.environ['PATH'][-1] != os.pathsep else ''}" +
                                       os.path.join(os.path.expanduser('~'), 'scoop', 'shims'))
            run_command(f'scoop install gh')
        else:
            raise NotImplementedError(f"Unsupported operating system: {PLATFORM}")

        print("> GitHub CLI installed successfully.")


def authenticate_gh():
    """Authenticates gh CLI."""
    try:
        result = run_command("gh auth status", text=True)
        if "Logged in to github.com" in result.stdout:
            return  # Skip authentication if already logged in
    except RuntimeError:
        pass

    try:
        print("> Setting up GitHub authentication...")
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as fd:
            gh_token = getpass.getpass("Tip: you can generate a Personal Access Token here https://github.com/settings/tokens\n"
                                       "The minimum required scopes are 'repo', 'read:org', 'workflow'.\n"
                                       "Paste your authentication token: ")
            fd.write(gh_token)
        if PLATFORM == "windows":
            run_command(f'Get-Content -Path "{fd.name}" | gh auth login --with-token', capture_output=False)
        else:
            run_command(f"gh auth login --with-token < {fd.name}", capture_output=False)
    except Exception as e:
        raise RuntimeError(f"Github authentication failed: {e}") from e
    finally:
        os.unlink(fd.name)


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


def add_license_file():
    if Path('LICENSE').exists():
        return

    try:
        pyproj_values = parse_pyproject_toml(keys=["license"])
        gh_cmd = f'gh api licenses/{pyproj_values["license"]}'
        result = run_command(gh_cmd, text=True)
        if result.returncode != 0:
            raise Exception(f"License api fetch failed with return code: {result.returncode}\n{result.stderr}")

        license_data = json.loads(result.stdout)
        license_body = license_data['body']
        with open('LICENSE', 'w') as license_file:
            license_file.write(license_body)
    except:
        print(f'Problem writing license file. Skipping...')


def initialize_git_repo():
    """Initializes git repository and sets up GitHub repository."""
    try:
        if Path('.git').exists():
            print(f'> A git repo already exists in the current directory!')
        else:
            print("> Initializing Git repository...")
            run_command('git config --global --add safe.directory "*"')  # you should be the main/only user on your computer
            run_command("git config --global init.defaultBranch main")
            run_command("git init")
            run_command("git add -A")
            run_command('git commit -m "chore: initial commit from copier-numpy"')
        try:
            run_command("gh repo view")
            print("> GitHub repo is already initialized!")
        except RuntimeError:
            print("> Creating GitHub repository and pushing code...")
            try:
                run_command(f'git remote rm origin')
            except:
                pass  # Just need to make sure the 'origin' remote name is free before pushing
            run_command(f'gh repo create --public --remote=origin --source=. --push')

    except Exception as e:
        raise RuntimeError(f"Git setup failed: {e}") from e


def initialize_git_repo_settings():
    """Use all the good defaults for the GitHub repository."""
    try:
        # Setup github pages
        if Path(".github/workflows/docs.yml").exists():
            try:
                # Create the gh-pages branch and link to Github pages (might fail if it already exists)
                run_command("git branch gh-pages")
                run_command("git push --set-upstream origin gh-pages")
                # run_command('gh api --method POST "/repos/{owner}/{repo}/pages" -f "source[branch]=gh-pages"')
                # I think pushing the gh-pages branch to remote automatically creates the GitHub pages site
            except:
                print('Problem setting up GitHub Pages -- may already exist. Skipping...')

        # Add Github basic settings
        pyproj_values = parse_pyproject_toml(keys=["description"])
        topics = [f"--add-topic {topic}" for topic in ["pdm", "python", "copier-template", "numpy"]]
        extra_options = ["--delete-branch-on-merge", "--enable-discussions", "--enable-issues", "--enable-wiki=false",
                         "--enable-projects=false", "--enable-merge-commit=false", "--enable-rebase-merge",
                         "--enable-squash-merge", "--allow-update-branch",
                         f'--description="{pyproj_values["description"]}"']
        gh_cmd = f'gh repo edit {" ".join(topics)} {" ".join(extra_options)}'
        run_command(gh_cmd)

        # Setup main and v* ruleset protections
        gh_cmd = 'gh api --method POST "/repos/{owner}/{repo}/rulesets" --input'
        for rule_name in ['main', 'vtag']:
            rule_file = f"https://raw.githubusercontent.com/eckelsjd/copier-numpy/main/.github/protect-{rule_name}.json"
            if PLATFORM == 'windows':
                ps_cmd = f'(Invoke-WebRequest -Uri {rule_file} -UseBasicParsing).Content | {gh_cmd} -'
                run_command(ps_cmd)
            else:
                run_command(f"curl -sSL {rule_file} | {gh_cmd} -")
    except Exception as e:
        raise RuntimeError(f"Initializing Github repo settings failed: {e}") from e


def initialize_pre_commit():
    if Path(".pre-commit-config.yaml").exists():
        print("> Initializing pre-commit config...")
        run_command("pdm run pre-commit install")


if __name__ == "__main__":
    if Path('.git').exists():
        response = input('> Found an existing .git repository. Do you want to skip GitHub set up? [Y/n]: ')
        if not response or response.lower().startswith('y'):
            print('Best of luck out there.')
            sys.exit(0)

    print('======================Running GitHub setup script======================')
    install_gh_cli()
    authenticate_gh()
    add_license_file()
    initialize_git_repo()
    initialize_git_repo_settings()
    initialize_pre_commit()
    print('======================Here is a summary of your repo======================')
    run_command('gh repo view', capture_output=False)
    print('======================GitHub repo is set up successfully!======================')
