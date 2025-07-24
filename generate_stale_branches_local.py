import os
import subprocess
import sys
import yaml
import shutil
import stat
from datetime import datetime, timedelta
from pathlib import Path

def load_config(config_path="config.yaml"):
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def run(cmd, cwd=None, env=None, capture_output=True):
    print(f"[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True,
        shell=isinstance(cmd, str)
    )
    if result.returncode != 0:
        if capture_output:
            print(f"[ERROR] Command failed:\n{result.stderr.strip()}")
        else:
            print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(1)
    return result.stdout.strip() if capture_output else ""

def clone_repo(clone_url, target_dir):
    if target_dir.exists():
        print(f"[INFO] Repo already cloned at {target_dir}, pulling latest.")
        run(["git", "fetch", "--all"], cwd=target_dir)
        run(["git", "checkout", "main"], cwd=target_dir)
        run(["git", "pull"], cwd=target_dir)
    else:
        print(f"[INFO] Cloning {clone_url} into {target_dir}")
        run(["git", "clone", clone_url, str(target_dir)])

def set_remote_url_with_token(repo_dir, remote_name, clone_url_with_token):
    run(["git", "remote", "set-url", remote_name, clone_url_with_token], cwd=repo_dir)
    print(f"[INFO] Updated remote {remote_name} to use token-authenticated URL.")

def create_branch_and_backdated_commit(repo_dir, base_branch, new_branch, days_ago, dry_run=False):
    run(["git", "checkout", base_branch], cwd=repo_dir)

    branches_output = run(["git", "branch", "-a"], cwd=repo_dir)
    if new_branch in branches_output:
        print(f"[INFO] Branch {new_branch} already exists. Checking out.")
        run(["git", "checkout", new_branch], cwd=repo_dir)
    else:
        print(f"[INFO] Creating and checking out {new_branch} from {base_branch}")
        run(["git", "checkout", "-b", new_branch], cwd=repo_dir)

    # Create or update dummy file
    file_name = f"testfile_{new_branch}.txt"
    file_path = repo_dir / file_name
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"Update for {new_branch} at simulated {days_ago} days ago.\n")

    # Stage the file
    run(["git", "add", file_name], cwd=repo_dir)

    # Backdate commit
    backdate = datetime.now() - timedelta(days=days_ago)
    backdate_str = backdate.strftime("%Y-%m-%dT%H:%M:%S")

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = backdate_str
    env["GIT_COMMITTER_DATE"] = backdate_str

    try:
        run(["git", "commit", "-m", f"Update test file on {new_branch} simulating {days_ago} days ago"], cwd=repo_dir, env=env)
    except SystemExit:
        print(f"[INFO] No changes to commit on {new_branch}. Skipping commit.")

    if dry_run:
        print(f"[DRY-RUN] Would pull, rebase, and push branch {new_branch}.")
        return

    # Pull with rebase
    try:
        run(["git", "pull", "--rebase", "origin", new_branch], cwd=repo_dir)
    except SystemExit:
        print(f"[ERROR] Rebase failed on {new_branch}. Resolve manually if needed.")
        sys.exit(1)

    # Push updated branch
    run(["git", "push", "origin", new_branch], cwd=repo_dir)
    print(f"[SUCCESS] Pushed {new_branch} with backdated commit after rebase.")

def handle_remove_readonly(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def safe_remove_directory(path):
    try:
        shutil.rmtree(path, onerror=handle_remove_readonly)
        print(f"[CLEANUP] Removed temporary repo directory: {path}")
    except Exception as e:
        print(f"[WARNING] Failed to remove {path}. Error: {e}")

def main():
    config = load_config()
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("[ERROR] GITHUB_TOKEN environment variable not set.")
        sys.exit(1)

    # Read using new structure
    repo_config = config["repository"]
    test_config = config["test_branch_generator"]
    options_config = config["options"]

    owner = repo_config["owner"]
    repo_name = repo_config["name"]
    repo_clone_url = repo_config["clone_url"]
    base_branch = repo_config.get("base_branch", "main")

    stale_days_list = test_config.get("stale_days_list", [60, 90])
    orphan_branch_names = test_config.get("orphan_branch_names", [])
    dry_run = options_config.get("dry_run", False)

    # Inject token into HTTPS clone URL
    if repo_clone_url.startswith("https://"):
        repo_clone_url_with_token = repo_clone_url.replace(
            "https://",
            f"https://{github_token}:x-oauth-basic@"
        )
    else:
        print("[ERROR] repo_clone_url must start with https://")
        sys.exit(1)

    repos_dir = Path.cwd() / "repos"
    repos_dir.mkdir(exist_ok=True)
    repo_dir = repos_dir / repo_name

    clone_repo(repo_clone_url_with_token, repo_dir)
    set_remote_url_with_token(repo_dir, "origin", repo_clone_url_with_token)

    for days in stale_days_list:
        branch_name = f"stale-{days}-days"
        create_branch_and_backdated_commit(repo_dir, base_branch, branch_name, days, dry_run)

    for ob_branch in orphan_branch_names:
        create_branch_and_backdated_commit(repo_dir, base_branch, ob_branch, 10, dry_run)

    safe_remove_directory(repo_dir)
    print("[INFO] All branches created/updated with backdated commits and cleanup completed.")

if __name__ == "__main__":
    main()
