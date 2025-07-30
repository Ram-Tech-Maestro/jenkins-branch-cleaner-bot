# 🧹 GitHub Branch Cleaner Bot — Jenkins-Driven Automation

A fully automated, Jenkins-integrated bot that scans GitHub repositories for **stale** and **orphaned branches**, logs detailed markdown reports, and archives them for review — all configurable via a centralized YAML file.

---

## 📌 Purpose

Maintaining clean and manageable Git branches is critical to collaboration and DevOps efficiency.  
Over time, feature branches become stale or disconnected (orphaned), bloating the repo and risking conflicts.

This tool solves that by:

- 🔎 Identifying **stale branches** based on inactivity
- 🧩 Detecting **orphaned branches** (no open/merged PRs)
- 📄 Generating a professional report in Markdown
- 📦 Archiving the report via Jenkins after every run
- 💬 Future-ready for GitHub issue alerts and Slack integration

---

## 🧰 Features at a Glance

| Feature | Description |
|--------|-------------|
| 🔍 Stale Branch Detection | Flags branches with no recent commits |
| 🔗 Orphan Detection | Flags branches without associated PRs |
| ⚙️ YAML-Based Configuration | Easily adjust thresholds, exclusions, output |
| 🐍 Python Bot | Lightweight and GitHub API-powered |
| ⚙️ Jenkins CI Integration | End-to-end automation on every scheduled run |
| 📁 Markdown Report | Developer-readable report in Markdown format |
| 🧪 Local Testing Utility | Simulate stale/orphan branches for dry runs |

---

## 📦 Project Structure

```
jenkins-branch-cleaner-bot/
├── Jenkinsfile                     # Jenkins pipeline
├── cleanup_bot.py                 # Main cleanup logic
├── generate_stale_branch_local.py # Test data simulation (optional)
├── config.yaml                    # Central config (thresholds, exclusions)
├── stale_orphan_branches_report.md # Auto-generated report
├── requirements.txt               # Python deps
└── README.md                      # This documentation
```

---

## 🚀 How It Works

### 🔁 Workflow Summary

1. **Checkout** repo via Jenkins
2. **Install** dependencies
3. **Run** `cleanup_bot.py`:
    - Fetches all branches from the target GitHub repo
    - Checks last commit dates
    - Compares against configured `stale_days_threshold`
    - Identifies orphaned branches via PR association checks
4. **Generate** `stale_orphan_branches_report.md`
5. **Archive** the report as a Jenkins build artifact

---

## 🛠️ Configuration (`config.yaml`)

```yaml
repository:
  owner: Ram-Tech-Maestro
  name: branch-cleaner-test-repo
  clone_url: https://github.com/Ram-Tech-Maestro/branch-cleaner-test-repo.git
  base_branch: main

options:
  dry_run: false
  log_level: INFO
  timezone: Asia/Kolkata

test_branch_generator:
  stale_days_list:
    - 60
    - 90
  orphan_branch_names:
    - orphan-branch-1
    - orphan-branch-2

cleanup_bot:
  stale_days_threshold: 45
  grace_period_days: 7
  excluded_branches:
    - main
    - dev
    - release/*
  notification_issue_title: "[BOT] Stale Branch Notification"
  log_file: stale_orphan_branches_report.md
```

> ✅ Customize thresholds, exclusions, dry run flags, and report output here.

---

## 🔗 Jenkins Pipeline

This project is designed to run fully automated through Jenkins. The pipeline handles workspace cleaning, dependency installation in a Python virtual environment, branch scanning, and report archival.

### 🧩 Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        GITHUB_TOKEN = credentials('GITHUB_PAT') // Jenkins credential ID
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                git url: 'https://github.com/Ram-Tech-Maestro/jenkins-branch-cleaner-bot.git', branch: 'main'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Cleanup Bot') {
            steps {
                sh '''
                    . venv/bin/activate
                    python cleanup_bot.py
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Cleanup bot ran successfully.'
        }
        failure {
            echo '❌ Cleanup bot failed. Check logs.'
        }
        always {
            archiveArtifacts artifacts: 'stale_orphan_branches_report.md', onlyIfSuccessful: true
        }
    }
}
```

### 🛠 Jenkins Integration Overview

This bot is intended to run as a **scheduled Jenkins job**, allowing fully automated GitHub branch maintenance.

#### 🧾 Key Jenkins Steps

| Stage | Description |
|-------|-------------|
| 🧼 `Clean Workspace` | Clears old build files to ensure a fresh start |
| 📥 `Checkout` | Clones the bot code from GitHub |
| 📦 `Install Dependencies` | Sets up a clean Python environment and installs dependencies from `requirements.txt` |
| 🚀 `Run Cleanup Bot` | Executes the bot to scan, analyze, and generate reports |
| 📁 `Archive Report` | Uploads `stale_orphan_branches_report.md` as a build artifact for download/review |

### 🧩 Prerequisites on Jenkins

- ✅ **Python 3.8+** must be available on the Jenkins agent
- ✅ **GitHub Personal Access Token (PAT)** must be added in Jenkins → Credentials  
  - Credential ID: `GITHUB_PAT`
- ✅ **Schedule the Job** via Jenkins “Build Periodically” (e.g., `H 2 * * 0` for every Sunday at 2AM)
- ✅ Jenkins agents must have internet access to install packages and call GitHub API

---

## 📄 Sample Markdown Report Output

```markdown
# 🧹 Stale & Orphan Branches Report for `branch-cleaner-test-repo`

_Generated: 2025-07-24T17:28:44.597532+00:00_

## 🚩 Stale Branches (> 45 days of inactivity)
- `stale-60-days` (Last commit: 2025-05-25)
- `stale-90-days` (Last commit: 2025-04-25)

## 🗃️ Orphan Branches (No PRs found)
- `orphan-branch-1`
- `orphan-branch-2`
- `stale-60-days`
- `stale-90-days`
```

> 📁 This file is archived in Jenkins → Available under build artifacts.

---

## 🧪 Simulate Test Branches (Local Testing)

Generate dummy branches for validation without touching remote:

```bash
python3 generate_stale_branch_local.py
```

You can modify the branch names and timestamps inside the script or YAML.

---

## 📥 Installation (For Local Runs)

### Requirements

- Python 3.8+
- GitHub Personal Access Token (PAT)
- Internet access

### Steps

```bash
git clone https://github.com/Ram-Tech-Maestro/jenkins-branch-cleaner-bot.git
cd jenkins-branch-cleaner-bot
pip3 install -r requirements.txt
export GITHUB_TOKEN=your_token_here
python3 cleanup_bot.py
```

---

## 📈 Future Enhancements

| Feature | Status |
|--------|--------|
| 🔔 GitHub Issue Notifications for stale branches | 🟡 Planned |
| 🗑️ Auto-delete mode with safety grace period | 🟡 Planned |
| 📬 Slack/MS Teams Notifications | 🔜 |
| 📊 Web dashboard for historical trend tracking | 🔜 |
| 🌐 GitHub Actions support | 🔜 |

---

## 🛡️ License

This project is proprietary and all rights are reserved.

Unauthorized copying, modification, redistribution, or use of any part of this repository is strictly prohibited without explicit written permission from the owner.

© 2025 Ram-Tech-Maestro. All rights reserved.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss your ideas.

For any questions, feel free to raise an issue or contact the maintainer directly.
