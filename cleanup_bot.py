import os
import sys
import yaml
from datetime import datetime, timezone, timedelta
from github import Github
from github.GithubException import GithubException

def load_config(config_path="config.yaml"):
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {config_path}: {e}")
        sys.exit(1)

def main():
    config = load_config()

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("[ERROR] GITHUB_TOKEN environment variable not set.")
        sys.exit(1)

    g = Github(github_token)

    # Read from refactored config
    repo_owner = config["repository"]["owner"]
    repo_name = config["repository"]["name"]

    cleanup_config = config["cleanup_bot"]
    stale_days_threshold = cleanup_config.get("stale_days_threshold", 45)
    grace_period_days = cleanup_config.get("grace_period_days", 7)
    excluded_branches = cleanup_config.get("excluded_branches", ["main", "master", "develop"])
    notification_issue_title = cleanup_config.get("notification_issue_title", "[BOT] Stale Branch Notification")
    report_file = cleanup_config.get("log_file", "stale_orphan_branches_report.md")

    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    print(f"[INFO] Connected to repository: {repo_owner}/{repo_name}")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=stale_days_threshold)
    stale_branches = []
    orphan_branches = []

    for branch in repo.get_branches():
        branch_name = branch.name

        # Skip excluded branches
        if any([
            branch_name == ex or (ex.endswith("/*") and branch_name.startswith(ex[:-2]))
            for ex in excluded_branches
        ]):
            continue

        try:
            commits = repo.get_commits(sha=branch_name)
            last_commit_date = commits[0].commit.committer.date

            if last_commit_date < cutoff_date:
                # Check for open PRs targeting this branch
                try:
                    open_prs = repo.get_pulls(state='open', base=branch_name)
                    if open_prs.totalCount > 0:
                        continue
                except GithubException as e:
                    print(f"[WARNING] Skipping PR check for {branch_name}: {e}")

                # Check if the branch has been merged via PR
                merged_prs = repo.get_pulls(state='closed', head=f"{repo_owner}:{branch_name}")
                if any(pr.is_merged() for pr in merged_prs):
                    continue

                stale_branches.append({
                    "branch": branch_name,
                    "last_commit": last_commit_date.isoformat()
                })

            # Check if orphan (no open or closed PRs from this branch)
            open_prs_head = repo.get_pulls(state='open', head=f"{repo_owner}:{branch_name}")
            closed_prs_head = repo.get_pulls(state='closed', head=f"{repo_owner}:{branch_name}")
            if open_prs_head.totalCount == 0 and closed_prs_head.totalCount == 0:
                orphan_branches.append({
                    "branch": branch_name,
                    "last_commit": last_commit_date.isoformat()
                })

        except GithubException as e:
            print(f"[WARNING] Skipping branch {branch_name}: {e}")
            continue

    # Write structured report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 🧹 Stale & Orphan Branches Report for `{repo_name}`\n\n")
        f.write(f"_Generated: {datetime.now(timezone.utc).isoformat()}_\n\n")

        if stale_branches:
            f.write(f"## 🚩 Stale Branches (> {stale_days_threshold} days of inactivity)\n")
            for sb in stale_branches:
                f.write(f"- `{sb['branch']}` (Last commit: `{sb['last_commit']}`)\n")
            f.write("\n")
        else:
            f.write("✅ No stale branches found.\n\n")

        if orphan_branches:
            f.write("## 🗃️ Orphan Branches (No PRs found)\n")
            for ob in orphan_branches:
                f.write(f"- `{ob['branch']}` (Last commit: `{ob['last_commit']}`)\n")
            f.write("\n")
        else:
            f.write("✅ No orphan branches found.\n\n")

    print(f"[INFO] Stale & orphan branches report written to `{report_file}`.")
    print("[INFO] Cleanup analysis completed without deletion as requested.")

if __name__ == "__main__":
    main()
