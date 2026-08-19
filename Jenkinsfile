pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    environment {
        IMAGE_NAME = 'yulietrojas/mi-microservicio'
        HELM_VALUES_FILE = 'helm/values-dev.yaml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.SHORT_COMMIT}"
                    env.LAST_COMMIT_MESSAGE = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    env.SKIP_PIPELINE = env.LAST_COMMIT_MESSAGE.contains('[skip jenkins]') ? 'true' : 'false'
                }
            }
        }

        stage('Install dependencies') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                python3 -m venv .venv
                . .venv/bin/activate
                pip install --upgrade pip
                pip install -r app/requirements.txt -r requirements-dev.txt
                '''
            }
        }

        stage('Static analysis') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                . .venv/bin/activate
                flake8 app tests --max-line-length=100 --extend-ignore=E203,W503
                '''
            }
        }

        stage('Unit tests') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                . .venv/bin/activate
                pytest tests -v
                '''
            }
        }

        stage('Build Docker image') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                dir('app') {
                    sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
                }
            }
        }

        stage('Validate Helm chart') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                tar -C "$WORKSPACE" -cf - helm | docker run --rm -i --entrypoint sh alpine/helm:3.16.1 -c "mkdir -p /workspace && tar -xf - -C /workspace && helm lint /workspace/helm -f /workspace/helm/values-dev.yaml"
                '''
            }
        }

        stage('Publish Docker image') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh '''
                    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Update GitOps manifest') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASSWORD')]) {
                    sh '''
                    git config user.name "Jenkins"
                    git config user.email "jenkins@local"
                    sed -i "s|repository: .*|repository: ${IMAGE_NAME}|" ${HELM_VALUES_FILE}
                    sed -i "s|tag: .*|tag: \"${IMAGE_TAG}\"|" ${HELM_VALUES_FILE}
                    git add ${HELM_VALUES_FILE}

                    if git diff --cached --quiet; then
                      echo "No hubo cambios en ${HELM_VALUES_FILE}."
                    else
                      git commit -m "ci: actualizar imagen a ${IMAGE_TAG} [skip jenkins]"
                      git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/yuliet719-beep/mi-microservicio.git HEAD:main
                    fi
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
            cleanWs()
        }
        success {
            echo 'Pipeline CI/CD completado: validaciones ejecutadas, imagen publicada y manifiesto GitOps actualizado.'
        }
        failure {
            echo 'Pipeline CI/CD falló. Revise el stage que reportó el error antes de publicar o desplegar cambios.'
        }
    }
}
