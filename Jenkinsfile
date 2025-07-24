pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
            args '-u root' // to allow pip installs if needed
        }
    }

    environment {
        GITHUB_TOKEN = credentials('GITHUB_PAT') // Jenkins credential ID
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/Ram-Tech-Maestro/jenkins-branch-cleaner-bot.git', branch: 'main'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python --version
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Cleanup Bot') {
            steps {
                sh '''
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
