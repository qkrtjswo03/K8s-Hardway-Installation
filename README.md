# K8s-Hardway-Installation

# (작성중 현재 아래 적힌 것은 예시로 적어둔 것 입니다.)

## Hardway Kubernetes Deployment Scripts

## 📚 개요 (Overview)

이 프로젝트는 **Kubernetes 클러스터를 HardWay 방식으로 구축**하기 위한 자동화 스크립트 모음입니다. 각 구성 요소를 수동으로 설정하는 대신, Python 기반 스크립트를 통해 인증서 생성, 전송, 노드 초기화 및 네트워크 구성 작업을 효율적으로 처리합니다.


## 🛠 주요 기능 (Key Features)


- Bastion 서버를 중심으로 인증서 생성 및 노드 전송 자동화
- Master 및 Worker 노드의 Kubernetes 구성 요소 자동 설정
- TLS Bootstrapping 및 RBAC 설정 스크립트 제공
- **Cilium**을 활용한 네트워크 플러그인 설정 및 배포
- Python 기반 스크립트와 `poetry`를 통한 의존성 및 환경 관리

---

## 📂 디렉토리 구조 (Directory Structure)

```plaintext
.
├── certs/                          # 인증서 저장 디렉토리
├── scripts/                        # 주요 스크립트 파일
│   ├── cert_generation.py          # 인증서 생성 스크립트
│   ├── etcd_setup.py               # etcd 설치 및 설정 스크립트
│   ├── etcd_verification.py        # etcd 검증 스크립트
│   ├── k8s_control_plane_setup.py  # Control Plane 설정 스크립트
│   ├── worker_cert_create.py       # Worker 노드 인증서 생성 및 전송 스크립트
│   ├── worker_node_setup.py        # Worker 노드 초기화 스크립트 (Worker Node 1)
│   ├── sub_worker_node_setup.py    # Worker 노드 초기화 스크립트 (다른 Worker Nodes)
│   ├── tls_setup.py                # TLS Bootstrapping 설정 스크립트
│   ├── sub_worker_cert_transfer.py # 추가 Worker 노드 인증서 전송 스크립트
│   ├── bastion_cilium_setup.py     # Bastion 노드에서 Cilium 설정
├── pyproject.toml                  # Poetry 프로젝트 설정 파일
├── README.md                       # 프로젝트 설명 문서
└── .env.example                    # 환경 변수 설정 예제 파일
```

---

## 📋 요구사항 (Requirements)

- **Python** >= 3.10
- **Poetry** >= 1.6.0
- **SSH 접근 권한**: Bastion에서 각 노드로 SSH 접속 가능해야 함
- **필수 Python 패키지**:
  - `paramiko`: SSH 연결 관리
  - `scp`: 파일 전송 관리

---

## 🚀 설치 및 실행 방법 (Installation & Usage)

### 1. 의존성 설치

```bash
# 리포지토리 클론
$ git clone https://git.company.com/repo/hardway-k8s-scripts.git
$ cd hardway-k8s-scripts

# Poetry 환경 설정 및 의존성 설치
$ poetry install
```

### 2. 환경 변수 설정
`.env.example` 파일을 참고하여 `.env` 파일을 생성하고, 필요한 환경 변수를 설정합니다.

```plaintext
SSH_USER=root
SSH_PASSWORD=your_password
CERT_DIR=/path/to/certs
```

### 3. Bastion 서버에서 인증서 생성 및 전송
1. 인증서를 생성하고 전송하려면 Bastion 서버에서 `cert_generation.py` 스크립트를 실행합니다.

```bash
$ poetry run python scripts/cert_generation.py
```

2. 생성된 인증서를 각 노드로 전송합니다.

```bash
$ poetry run python scripts/worker_cert_create.py
```

### 4. Master 노드 설정
각 Master 노드에서 `etcd_setup.py` 및 `k8s_control_plane_setup.py`를 실행하여 etcd와 Control Plane을 설정합니다.

```bash
$ poetry run python scripts/etcd_setup.py
$ poetry run python scripts/k8s_control_plane_setup.py
```

### 5. Worker 노드 설정
1. 첫 번째 Worker 노드에서 `worker_node_setup.py`를 실행하여 초기 설정을 완료합니다.

```bash
$ poetry run python scripts/worker_node_setup.py
```

2. 추가 Worker 노드에서 `sub_worker_cert_transfer.py`로 인증서를 전송한 뒤, `sub_worker_node_setup.py`를 실행합니다.

```bash
$ poetry run python scripts/sub_worker_cert_transfer.py
$ poetry run python scripts/sub_worker_node_setup.py
```

### 6. Cilium 설치 및 설정
Bastion 서버에서 `bastion_cilium_setup.py` 스크립트를 실행하여 Cilium을 설치하고 네트워크 플러그인을 구성합니다.

```bash
$ poetry run python scripts/bastion_cilium_setup.py
```

---

## 🧰 주요 스크립트 설명 (Scripts Description)

### 1. `cert_generation.py`
- **기능**: 인증서를 생성하여 Bastion 서버에 저장합니다.
- **설명**: OpenSSL을 사용하여 CA 인증서, SAN 인증서 및 kubeconfig 파일을 생성합니다.
- **로그**: `/root/hardway/certs/cert_generation.log`

### 2. `worker_cert_create.py`
- **기능**: Worker 노드에 필요한 인증서를 생성하고 전송합니다.
- **설명**: OpenSSL로 노드 인증서를 생성하고, SCP를 통해 전송합니다.

### 3. `etcd_setup.py`
- **기능**: 각 Master 노드에서 etcd를 설치 및 설정합니다.
- **설명**: etcd 바이너리를 다운로드하고 systemd 서비스를 생성합니다.

### 4. `k8s_control_plane_setup.py`
- **기능**: Control Plane 구성 요소를 설치하고 구성합니다.
- **설명**: kube-apiserver, kube-scheduler, kube-controller-manager의 systemd 서비스를 생성합니다.

### 5. `worker_node_setup.py` / `sub_worker_node_setup.py`
- **기능**: Worker 노드를 초기화하고 설정합니다.
- **설명**: Docker 설치, kubelet 및 kube-proxy 설정, CNI 플러그인 설치 등을 수행합니다.

### 6. `tls_setup.py`
- **기능**: TLS Bootstrapping을 위한 RBAC 및 토큰을 설정합니다.

### 7. `bastion_cilium_setup.py`
- **기능**: Bastion 서버에서 Helm을 사용하여 Cilium을 설치하고 네트워크 플러그인을 설정합니다.

---

## 📦 의존성 관리 (Dependency Management)

### Poetry 명령어 예시

```bash
# 의존성 추가
$ poetry add <패키지명>

# 개발용 의존성 추가
$ poetry add --dev <패키지명>

# 의존성 설치
$ poetry install

# Poetry 환경에 진입
$ poetry shell
```

---

## 🔧 문제 해결 (Troubleshooting)

### 1. 인증서 전송 실패
- **원인**: Bastion 서버에서 노드로의 SSH 접근 문제
- **해결 방법**:
  - 노드에서 SSH 설정을 확인 (`PermitRootLogin yes` 및 `PasswordAuthentication yes` 활성화)

### 2. Cilium 설치 오류
- **원인**: Helm 버전 문제 또는 네트워크 대역 충돌
- **해결 방법**:
  - Helm 버전을 확인하고 최신 버전을 설치
  - `cilium-config`에서 Pod CIDR을 명시적으로 설정

### 3. etcd 서비스 실패
- **원인**: 인증서 경로 문제
- **해결 방법**:
  - `/etc/ssl/etcd/ssl/` 디렉토리에 올바른 인증서가 있는지 확인

---
>>>>>>> f4cd830 (K8s-Hardway-Install 스크립트)
