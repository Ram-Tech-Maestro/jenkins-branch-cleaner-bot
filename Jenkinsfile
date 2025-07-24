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
        stage('Checkout') {
            steps {
                git url: 'https://github.com/Ram-Tech-Maestro/jenkins-branch-cleaner-bot.git', branch: 'main'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    pip3 install --upgrade pip
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Cleanup Bot') {
            steps {
                sh '''
                    python3 cleanup_bot.py
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
