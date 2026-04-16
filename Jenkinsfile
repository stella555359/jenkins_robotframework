pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
    }

    environment {
        DEPLOY_HOST = '10.71.210.104'
        DEPLOY_USER = 'ute'
        DEPLOY_PATH = '/opt/jenkins_robotframework'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/stella555359/jenkins_robotframework.git'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                    set -e
                    cd ${DEPLOY_PATH}
                    git fetch origin
                    git checkout main
                    git pull --ff-only origin main
                    chmod +x deploy/scripts/deploy_all.sh
                    bash deploy/scripts/deploy_all.sh
                '
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                ssh ${DEPLOY_USER}@${DEPLOY_HOST} '
                    curl --fail --noproxy localhost http://localhost:8000/health
                    curl --fail --noproxy localhost http://localhost:8001/health
                '
                '''
            }
        }
    }
}