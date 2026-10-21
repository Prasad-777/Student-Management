
pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out Student Management System source code'
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo 'Running automated tests'
                sh 'python -m pytest -v'
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker image'
                sh 'docker build -t student-management-app:v1 .'
            }
        }

        stage('Pipeline Success') {
            steps {
                echo 'All pipeline stages completed successfully!'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Tests passed and Docker image was built.'
        }

        failure {
            echo 'FAILURE: Check the Jenkins console output.'
        }

        always {
            echo 'Pipeline execution finished.'
        }
    }
}
