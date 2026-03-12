pipeline {
  agent any

  environment {
    DOCKERHUB_USER = 'zurang'
    REGISTRY = 'docker.io'
    NAMESPACE = 'flask-app'
    KUBECONFIG = credentials('kubeconfig-flask-msa')
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/HJ1235/flask-msa.git'
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

    stage('Docker Login') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh '''
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
          '''
        }
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/auth-service:${GIT_TAG}   ./services/auth-service
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/board-service:${GIT_TAG}  ./services/board-service
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/diary-service:${GIT_TAG}  ./services/diary-service
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/todos-service:${GIT_TAG}  ./services/todos-service
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/study-service:${GIT_TAG}  ./services/study-service
          docker build --no-cache -t ${REGISTRY}/${DOCKERHUB_USER}/admin-service:${GIT_TAG}  ./services/admin-service
        '''
      }
    }

    stage('Push Images') {
      steps {
        sh '''
          docker push ${REGISTRY}/${DOCKERHUB_USER}/auth-service:${GIT_TAG}
          docker push ${REGISTRY}/${DOCKERHUB_USER}/board-service:${GIT_TAG}
          docker push ${REGISTRY}/${DOCKERHUB_USER}/diary-service:${GIT_TAG}
          docker push ${REGISTRY}/${DOCKERHUB_USER}/todos-service:${GIT_TAG}
          docker push ${REGISTRY}/${DOCKERHUB_USER}/study-service:${GIT_TAG}
          docker push ${REGISTRY}/${DOCKERHUB_USER}/admin-service:${GIT_TAG}
        '''
      }
    }

    stage('Update Manifests') {
      steps {
        sh '''
          sed -i "s|image: docker.io/zurang/auth-service:.*|image: docker.io/zurang/auth-service:${GIT_TAG}|g"   services/auth-service/k8s/auth-service.yaml
          sed -i "s|image: docker.io/zurang/board-service:.*|image: docker.io/zurang/board-service:${GIT_TAG}|g" services/board-service/k8s/board-service.yaml
          sed -i "s|image: docker.io/zurang/diary-service:.*|image: docker.io/zurang/diary-service:${GIT_TAG}|g" services/diary-service/k8s/diary-service.yaml
          sed -i "s|image: docker.io/zurang/todos-service:.*|image: docker.io/zurang/todos-service:${GIT_TAG}|g" services/todos-service/k8s/todos-service.yaml
          sed -i "s|image: docker.io/zurang/study-service:.*|image: docker.io/zurang/study-service:${GIT_TAG}|g" services/study-service/k8s/study-service.yaml
          sed -i "s|image: docker.io/zurang/admin-service:.*|image: docker.io/zurang/admin-service:${GIT_TAG}|g" services/admin-service/k8s/admin-service.yaml
        '''
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          export KUBECONFIG=$KUBECONFIG

          kubectl apply -f k8s/namespace/namespace.yaml
          kubectl apply -f k8s/configmap/configmap-secret.yaml
          kubectl apply -f k8s/storage/storage.yaml
          kubectl apply -f k8s/rbac/rbac.yaml
          kubectl apply -f k8s/mysql/mysql.yaml

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
        '''
      }
    }

    stage('Rollout Check') {
      steps {
        sh '''
          export KUBECONFIG=$KUBECONFIG

          kubectl rollout status deployment/auth-service  -n ${NAMESPACE} --timeout=180s
          kubectl rollout status deployment/board-service -n ${NAMESPACE} --timeout=180s
          kubectl rollout status deployment/diary-service -n ${NAMESPACE} --timeout=180s
          kubectl rollout status deployment/todos-service -n ${NAMESPACE} --timeout=180s
          kubectl rollout status deployment/study-service -n ${NAMESPACE} --timeout=180s
          kubectl rollout status deployment/admin-service -n ${NAMESPACE} --timeout=180s
        '''
      }
    }
  }

  post {
    success {
      echo "CI/CD pipeline completed successfully. Tag: ${GIT_TAG}"
    }
    failure {
      echo "Pipeline failed. Check build/push/deploy logs."
    }
    always {
      sh 'docker logout docker.io || true'
    }
  }
}
