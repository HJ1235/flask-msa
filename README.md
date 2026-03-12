# Flask App - MSA Kubernetes CI/CD 프로젝트

## 전체 디렉토리 구조

```
flask-msa/
│
├── Jenkinsfile                          # 루트 파이프라인 (전체 서비스 통합 배포)
├── app.py                               # 원본 모놀리식 app.py (참고용)
│
├── services/                            # 마이크로서비스 모음
│   ├── auth-service/                    # 인증 서비스 (회원가입/로그인/로그아웃)
│   │   ├── Dockerfile
│   │   ├── Jenkinsfile                  # 서비스 독립 파이프라인
│   │   ├── app/
│   │   │   ├── app.py                   # Flask 엔트리포인트
│   │   │   ├── auth.py                  # 인증 Blueprint
│   │   │   ├── db.py                    # DB 연결
│   │   │   ├── utils.py                 # 공통 유틸
│   │   │   └── requirements.txt
│   │   └── k8s/
│   │       └── auth-service.yaml        # Deployment + Service
│   │
│   ├── board-service/                   # 게시판 서비스
│   │   ├── Dockerfile
│   │   ├── Jenkinsfile
│   │   ├── app/
│   │   │   ├── app.py
│   │   │   ├── board.py
│   │   │   ├── db.py
│   │   │   ├── utils.py
│   │   │   └── requirements.txt
│   │   └── k8s/
│   │       └── board-service.yaml
│   │
│   ├── diary-service/                   # 일기장 서비스
│   │   ├── Dockerfile
│   │   ├── Jenkinsfile
│   │   ├── app/
│   │   │   ├── app.py
│   │   │   ├── diary.py
│   │   │   ├── db.py
│   │   │   ├── utils.py
│   │   │   └── requirements.txt
│   │   └── k8s/
│   │       └── diary-service.yaml
│   │
│   ├── todos-service/                   # Todo 관리 서비스
│   │   ├── Dockerfile
│   │   ├── Jenkinsfile
│   │   ├── app/
│   │   │   ├── app.py
│   │   │   ├── todos.py
│   │   │   ├── db.py
│   │   │   ├── utils.py
│   │   │   └── requirements.txt
│   │   └── k8s/
│   │       └── todos-service.yaml
│   │
│   ├── study-service/                   # 학습 콘텐츠 조회 서비스
│   │   ├── Dockerfile
│   │   ├── Jenkinsfile
│   │   ├── app/
│   │   │   ├── app.py
│   │   │   ├── study.py
│   │   │   ├── db.py
│   │   │   ├── utils.py
│   │   │   └── requirements.txt
│   │   └── k8s/
│   │       └── study-service.yaml
│   │
│   └── admin-service/                   # 관리자 서비스 (콘텐츠/과목 관리)
│       ├── Dockerfile
│       ├── Jenkinsfile
│       ├── app/
│       │   ├── app.py
│       │   ├── admin.py
│       │   ├── db.py
│       │   ├── utils.py
│       │   └── requirements.txt
│       └── k8s/
│           └── admin-service.yaml
│
├── k8s/                                 # 공통 K8s 리소스
│   ├── namespace/
│   │   └── namespace.yaml               # flask-app, jenkins 네임스페이스
│   ├── rbac/
│   │   └── rbac.yaml                    # ServiceAccount, Role, ClusterRole
│   ├── configmap/
│   │   └── configmap-secret.yaml        # ConfigMap + Secret
│   ├── storage/
│   │   └── storage.yaml                 # PV, PVC, StorageClass
│   ├── mysql/
│   │   └── mysql.yaml                   # MySQL StatefulSet + Service
│   ├── network-policy/
│   │   └── network-policy.yaml          # 서비스 간 통신 정책
│   └── ingress/
│       └── ingress.yaml                 # 경로 기반 라우팅
│
└── jenkins/
    └── jenkins.yaml                     # Jenkins Deployment + Service + Pipeline ConfigMap
```

---

## 서비스 포트 구성

| 서비스 | 컨테이너 포트 | URL 경로 | 역할 |
|---|---|---|---|
| auth-service | 5000 | `/` | 회원가입, 로그인, 로그아웃, 비밀번호 재설정 |
| board-service | 5001 | `/board` | 게시글 CRUD, 댓글 |
| diary-service | 5002 | `/diary` | 일기 작성/조회, 달력 |
| todos-service | 5003 | `/todos` | Todo CRUD, 마감일 관리 |
| study-service | 5004 | `/study` | 학습 콘텐츠 조회 |
| admin-service | 5005 | `/admin` | 콘텐츠/과목 관리, 파일 업로드 |
| MySQL | 3306 | 내부 전용 | 데이터베이스 |
| Jenkins | 8080 | NodePort:30080 | CI/CD 파이프라인 |

---

## CI/CD 파이프라인 흐름

```
Git push
   │
   ▼
GitHub Webhook
   │
   ▼
Jenkins (루트 Jenkinsfile)
   │
   ├── 1. Checkout (git)
   ├── 2. 변경된 서비스 감지 (git diff)
   ├── 3. Docker 이미지 병렬 빌드
   ├── 4. Registry 푸시
   ├── 5. 공통 K8s 리소스 적용 (namespace/rbac/configmap/mysql)
   ├── 6. 변경된 서비스만 K8s 배포 (Rolling Update)
   └── 7. 배포 검증
         │
         ├── 성공 → 완료
         └── 실패 → 자동 롤백 (kubectl rollout undo)
```

---

## 배포 전 설정 체크리스트

### 1. 노드 라벨 설정
```bash
kubectl label node <앱-노드>    role=app
kubectl label node <DB-노드>    role=database disktype=ssd
kubectl label node <관리자-노드> role=admin
kubectl label node <CI/CD-노드> role=cicd
```

### 2. Secret 값 변경 (필수!)
```bash
# base64 인코딩
echo -n '새비밀번호' | base64

# 수정
kubectl edit secret flask-app-secret -n flask-app
```

### 3. 변경 필요 항목
| 파일 | 변경 항목 |
|---|---|
| `k8s/configmap/configmap-secret.yaml` | DB_PASSWORD, FLASK_SECRET_KEY, MYSQL_ROOT_PASSWORD |
| `k8s/ingress/ingress.yaml` | 도메인명, admin IP 화이트리스트 |
| `k8s/storage/storage.yaml` | NFS 서버 IP 또는 CSI 드라이버 |
| `services/*/k8s/*.yaml` | `docker.io/zurang` → 실제 레지스트리 주소 |
| `Jenkinsfile` | `docker.io/zurang`, credentialsId |

### 4. Jenkins Credentials 등록
- `registry-credentials` : Docker Registry 계정
- `kubeconfig-credentials` : kubectl 접근용 kubeconfig

### 5. 최초 배포 순서
```bash
kubectl apply -f k8s/namespace/namespace.yaml
kubectl apply -f k8s/rbac/rbac.yaml
kubectl apply -f k8s/configmap/configmap-secret.yaml
kubectl apply -f k8s/storage/storage.yaml
kubectl apply -f k8s/mysql/mysql.yaml
kubectl apply -f k8s/network-policy/network-policy.yaml
kubectl apply -f k8s/ingress/ingress.yaml
kubectl apply -f jenkins/jenkins.yaml

# 서비스 배포
for svc in auth board diary todos study admin; do
  kubectl apply -f services/${svc}-service/k8s/${svc}-service.yaml
done
```
