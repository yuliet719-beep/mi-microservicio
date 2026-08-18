pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = 'yulietrojas/mi-microservicio'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Clonar repositorio') {
            steps {
                git branch: 'main', url: 'https://github.com/yuliet719-beep/mi-microservicio.git'
            }
        }

        stage('Construir imagen Docker') {
            steps {
                dir('app') {
                    sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
                }
            }
        }

        stage('Publicar imagen en DockerHub') {
            steps {
                sh 'echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin'
                sh 'docker push ${IMAGE_NAME}:${IMAGE_TAG}'
                sh 'docker push ${IMAGE_NAME}:latest'
            }
        }
    }

    post {
        always {
            sh 'docker logout'
        }
        success {
            echo 'Pipeline CD completado: imagen publicada correctamente en DockerHub.'
        }
        failure {
            echo 'Pipeline CD falló. Revisar logs de la etapa correspondiente.'
        }
    }
}
