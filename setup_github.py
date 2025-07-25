"""This script will:

1) Install Github CLI (if needed)
2) Authenticate github
3) Create a license file
4) Start a local git repo and push to Github (if needed)
5) Give the Github remote repo some nice settings

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
import traceback
import shlex


PLATFORM = platform.system().lower()


def run_command(command, capture_output=True, text=None, shell=False):
    """Run a command using subprocess."""
    try:
        if PLATFORM == 'windows':
            command = ['powershell', '-command', command]
        else:
            if not shell:
                command = shlex.split(command)
        return subprocess.run(command, capture_output=capture_output, check=True, text=text, shell=shell)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command `{command}` failed with code {e.returncode}: {e}\nError message: {e.stderr}") from e
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Subprocess error: {e}") from e


def get_linux_distro():
    distro_url = "https://raw.githubusercontent.com/python-distro/distro/master/src/distro/distro.py"
    distro_file = "distro.py"
    run_command(f'curl -sSL {distro_url} > {distro_file}', shell=True)
    sys.path.append('.')
    import distro
    distro_id = distro.id().lower()
    os.unlink(distro_file)
    return distro_id


def install_gh_cli():
    """Installs GitHub CLI (gh) based on the operating system."""
    try:
        run_command("gh --version")
        print("> GitHub CLI is already installed.")
    except (FileNotFoundError, RuntimeError) as e:
        print("> Installing GitHub CLI...")
        if PLATFORM == "linux":
            print('> Attempt Linux install of GitHub CLI...')
            distro = get_linux_distro()
            if "ubuntu" in distro or "debian" in distro:
                linux_cmd = r'curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
                && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
                && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
                && sudo apt update \
                && sudo apt install gh -y'
                run_command(linux_cmd, capture_output=False, shell=True)
            elif "fedora" in distro or "centos" in distro or "rhel" in distro:
                run_command("sudo dnf install 'dnf-command(config-manager)' -y")
                run_command("sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo")
                run_command("sudo dnf install gh --repo gh-cli -y")
            else:
                print(f"Unsupported Linux distribution: {distro}. Please install GitHub CLI manually.")
                sys.exit(0)
        elif PLATFORM == "darwin":
            print('> Attempt MacOS install of Github CLI via brew...')
            try:
                run_command("brew --version")
            except FileNotFoundError:
                run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            run_command("brew install gh")
        elif PLATFORM == 'windows':
            print('> Attempt Windows install of Github CLI via scoop...')
            try:
                run_command(f'scoop --version')
            except (FileNotFoundError, RuntimeError):
                run_command('Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser')
                run_command('Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression')
                os.environ['PATH'] += (f"{os.pathsep if os.environ['PATH'][-1] != os.pathsep else ''}" +
                                       os.path.join(os.path.expanduser('~'), 'scoop', 'shims'))
            run_command(f'scoop install gh')
        else:
            print(f"Unsupported operating system: {PLATFORM}. Please setup your git repository manually.")
            sys.exit(0)

        print("> GitHub CLI installed successfully.")


def authenticate_gh():
    """Authenticates gh CLI."""
    try:
        result = run_command("gh auth status", text=True)
        if "Logged in to github.com" in result.stdout:
            return  # Skip authentication if already logged in
    except FileNotFoundError:
        print(f'GitHub CLI not installed properly: `gh auth status` failed.')
        sys.exit(0)
    except RuntimeError:
        pass  # If you are not logged in

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
            run_command(f"gh auth login --with-token < {fd.name}", capture_output=False, shell=True)
    except Exception as e:
        raise RuntimeError(f"GitHub authentication failed.") from e
    finally:
        os.unlink(fd.name)  # Ensure personal access token gets deleted


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
        result = run_command(f'gh api licenses/{pyproj_values["license"]}', text=True)
        license_data = json.loads(result.stdout)
        license_body = license_data['body']
        with open('LICENSE', 'w') as license_file:
            license_file.write(license_body)
    except Exception as e:
        print(f'Problem writing license file: {e}\nSkipping...')


def initialize_git_repo():
    """Initializes git repository and sets up GitHub repository."""
    if Path('.git').exists():
        print(f'> A git repo already exists in the current directory!')
    else:
        print("> Initializing Git repository...")

        # Make sure the repo will be listed as "safe"
        repo_path = Path('.').resolve().as_posix()
        git_cmd = f'git config --global --add safe.directory "{repo_path}"'
        try:
            result = run_command('git config --global --get-all safe.directory', text=True)
            safe_directories = result.stdout.strip().split('\n')
            safe_config_applied = False
            for safe_dir in safe_directories:
                if str(safe_dir) == str(repo_path):
                    safe_config_applied = True
            if not safe_config_applied:
                run_command(git_cmd)
        except RuntimeError:
            run_command(git_cmd)  # If safe.directory is empty or other error is encountered

        # run_command("git config --global init.defaultBranch main")
        run_command("git init")
        run_command("git checkout -b main")
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
        print("> GitHub repo has been created successfully!")


def initialize_git_repo_settings():
    """Use all the good defaults for the GitHub repository."""
    # Setup github pages
    print("> Setting up basic repository settings...")
    if Path(".github/workflows/docs.yml").exists():
        try:
            # Create the gh-pages branch and link to Github pages (might fail if it already exists)
            run_command("git branch gh-pages")
            run_command("git push --set-upstream origin gh-pages")  # automatically creates the GitHub pages site
            # run_command('gh api --method POST "/repos/{owner}/{repo}/pages" -f "source[branch]=gh-pages"')
        except Exception as e:
            print(f'Problem setting up GitHub Pages: {e}\nSkipping...')

    # Add Github basic settings
    try:
        pyproj_values = parse_pyproject_toml(keys=["description"])
        topics = [f"--add-topic {topic}" for topic in ["pdm", "python", "numpy"]]
        extra_options = ["--delete-branch-on-merge", "--enable-discussions", "--enable-issues", "--enable-wiki=false",
                         "--enable-projects=false", "--enable-merge-commit=false", "--enable-rebase-merge",
                         "--enable-squash-merge", "--allow-update-branch",
                         f'--description="{pyproj_values["description"]}"']
        gh_cmd = f'gh repo edit {" ".join(topics)} {" ".join(extra_options)}'
        run_command(gh_cmd)
    except Exception as e:
        print(f'Problem adding GitHub repo settings: {e}\nSkipping...')

    # Setup main and v* ruleset protections
    try:
        gh_cmd = 'gh api --method POST "/repos/{owner}/{repo}/rulesets" --input'
        for rule_name in ['main', 'vtag']:
            rule_file = f"https://raw.githubusercontent.com/eckelsjd/copier-numpy/main/.github/protect-{rule_name}.json"
            if PLATFORM == 'windows':
                ps_cmd = f'(Invoke-WebRequest -Uri {rule_file} -UseBasicParsing).Content | {gh_cmd} -'
                run_command(ps_cmd)
            else:
                run_command(f"curl -sSL {rule_file} | {gh_cmd} -", shell=True)
    except Exception as e:
        print(f'Problem adding branch and rule protections: {e}\nSkipping...')

    print('> All settings applied successfully!')


if __name__ == "__main__":
    try:
        if Path('.git').exists():
            response = input('> Found an existing .git repository. Do you want to skip GitHub set up? [Y/n]: ')
            if not response or response.lower().startswith('y'):
                print('Best of luck out there.')
                sys.exit(0)
        try:
            run_command('git --version')
        except FileNotFoundError:
            print(f'Git does not appear to be installed. Please install and try again.')
            sys.exit(0)

        print('======================Running GitHub setup script======================')
        install_gh_cli()
        authenticate_gh()
        add_license_file()
        initialize_git_repo()
        initialize_git_repo_settings()
        print('======================Here is a summary of your repo======================')
        run_command('gh repo view', capture_output=False)
        print('======================GitHub repo is set up successfully!======================')
    except Exception as e:
        print(f'======================An unknown error has occurred.======================')
        print(f'The following stack trace is provided for debugging purposes:\n\n')
        traceback.print_exc()
        print(f'======================Download the `setup_github.py` script from copier-numpy to try again.======================')
