pipeline {
  agent any

  environment {
    REMOTE_HOST = '10.10.8.3'
    REMOTE_USER = 'master'
    REMOTE_APP_DIR = '/home/master/flask-msa'
    DOCKERHUB_USER = 'zurang'
    NAMESPACE = 'flask-app'
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', credentialsId: 'github-creds', url: 'https://github.com/HJ1235/flask-msa.git'
      }
    }

    stage('Set Commit Tag') {
      steps {
        script {
          env.GIT_TAG = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
          echo "Using image tag: ${env.GIT_TAG}"
        }
      }
    }

    stage('Deploy via SSH on master') {
      steps {
        withCredentials([
          sshUserPrivateKey(credentialsId: 'master-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
          usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')
        ]) {
          sh '''
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "
              set -e
              cd ${REMOTE_APP_DIR}

              git fetch origin main
              git checkout main
              git pull origin main

              GIT_TAG=${GIT_TAG}

              echo '${DOCKER_PASS}' | docker login docker.io -u '${DOCKER_USER}' --password-stdin

              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/auth-service:${GIT_TAG}   ./services/auth-service
              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/board-service:${GIT_TAG}  ./services/board-service
              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/diary-service:${GIT_TAG}  ./services/diary-service
              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/todos-service:${GIT_TAG}  ./services/todos-service
              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/study-service:${GIT_TAG}  ./services/study-service
              docker build --no-cache -t docker.io/${DOCKERHUB_USER}/admin-service:${GIT_TAG}  ./services/admin-service

              docker push docker.io/${DOCKERHUB_USER}/auth-service:${GIT_TAG}
              docker push docker.io/${DOCKERHUB_USER}/board-service:${GIT_TAG}
              docker push docker.io/${DOCKERHUB_USER}/diary-service:${GIT_TAG}
              docker push docker.io/${DOCKERHUB_USER}/todos-service:${GIT_TAG}
              docker push docker.io/${DOCKERHUB_USER}/study-service:${GIT_TAG}
              docker push docker.io/${DOCKERHUB_USER}/admin-service:${GIT_TAG}

              sed -i \\"s|image: docker.io/zurang/auth-service:.*|image: docker.io/zurang/auth-service:${GIT_TAG}|g\\"   services/auth-service/k8s/auth-service.yaml
              sed -i \\"s|image: docker.io/zurang/board-service:.*|image: docker.io/zurang/board-service:${GIT_TAG}|g\\" services/board-service/k8s/board-service.yaml
              sed -i \\"s|image: docker.io/zurang/diary-service:.*|image: docker.io/zurang/diary-service:${GIT_TAG}|g\\" services/diary-service/k8s/diary-service.yaml
              sed -i \\"s|image: docker.io/zurang/todos-service:.*|image: docker.io/zurang/todos-service:${GIT_TAG}|g\\" services/todos-service/k8s/todos-service.yaml
              sed -i \\"s|image: docker.io/zurang/study-service:.*|image: docker.io/zurang/study-service:${GIT_TAG}|g\\" services/study-service/k8s/study-service.yaml
              sed -i \\"s|image: docker.io/zurang/admin-service:.*|image: docker.io/zurang/admin-service:${GIT_TAG}|g\\" services/admin-service/k8s/admin-service.yaml

              kubectl apply -f k8s/namespace/namespace.yaml
              kubectl apply -f k8s/configmap/configmap-secret.yaml
              kubectl apply -f k8s/rbac/rbac.yaml

              kubectl apply -f services/auth-service/k8s/auth-service.yaml
              kubectl apply -f services/board-service/k8s/board-service.yaml
              kubectl apply -f services/diary-service/k8s/diary-service.yaml
              kubectl apply -f services/todos-service/k8s/todos-service.yaml
              kubectl apply -f services/study-service/k8s/study-service.yaml
              kubectl apply -f services/admin-service/k8s/admin-service.yaml

              kubectl apply -f services/auth-service/k8s/auth-ingress.yaml
              kubectl apply -f services/board-service/k8s/board-ingress.yaml
              kubectl apply -f services/diary-service/k8s/diary-ingress.yaml
              kubectl apply -f services/todos-service/k8s/todos-ingress.yaml
              kubectl apply -f services/study-service/k8s/study-ingress.yaml
              kubectl apply -f services/admin-service/k8s/admin-ingress.yaml

              kubectl rollout status deployment/auth-service  -n ${NAMESPACE} --timeout=180s
              kubectl rollout status deployment/board-service -n ${NAMESPACE} --timeout=180s
              kubectl rollout status deployment/diary-service -n ${NAMESPACE} --timeout=180s
              kubectl rollout status deployment/todos-service -n ${NAMESPACE} --timeout=180s
              kubectl rollout status deployment/study-service -n ${NAMESPACE} --timeout=180s
              kubectl rollout status deployment/admin-service -n ${NAMESPACE} --timeout=180s

              docker logout docker.io || true
            "
          '''
        }
      }
    }
  }

  post {
    success {
      echo "CI/CD pipeline completed successfully. Tag: ${GIT_TAG}"
    }
    failure {
      echo "Pipeline failed. Check SSH/build/deploy logs."
    }
  }
}
