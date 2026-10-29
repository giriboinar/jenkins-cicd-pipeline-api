// Declarative Jenkins pipeline for the Deployment Tracker API.
// Stages: test -> security scan -> Docker build -> (gated) push -> (gated) deploy.
// The push and deploy stages only run when their flags are set to 'true',
// so a plain Jenkins run without registry/cluster credentials still goes green
// through build. See jenkins/setup.md for the Jenkins setup and credentials.
pipeline {
    agent any
    environment {
        IMAGE = 'deployment-tracker-api'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DOCKER_PUSH = 'false'
        DEPLOY_TO_K8S = 'false'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -q -r app/requirements.txt pytest==9.0.3 httpx==0.28.1
                    python -m pytest tests/ -q
                '''
            }
        }
        stage('Security Scan') {
            steps {
                sh 'trivy fs --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 .'
            }
        }
        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE}:${IMAGE_TAG} ."
            }
        }
        stage('Docker Push') {
            when {
                environment name: 'DOCKER_PUSH', value: 'true'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker tag ${IMAGE}:${IMAGE_TAG} $DOCKER_USER/${IMAGE}:${IMAGE_TAG}
                        docker push $DOCKER_USER/${IMAGE}:${IMAGE_TAG}
                    '''
                }
            }
        }
        stage('Deploy to Kubernetes') {
            when {
                environment name: 'DEPLOY_TO_K8S', value: 'true'
            }
            steps {
                sh '''
                    kubectl apply -f k8s/
                    kubectl rollout status deployment/deployment-tracker-api -n deployments --timeout=120s
                '''
            }
        }
    }
    post {
        always {
            sh 'docker rmi ${IMAGE}:${IMAGE_TAG} || true'
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded.'
        }
        failure {
            echo 'Pipeline failed - check the failing stage above.'
        }
    }
}
