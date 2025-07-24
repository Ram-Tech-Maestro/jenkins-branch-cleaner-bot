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
