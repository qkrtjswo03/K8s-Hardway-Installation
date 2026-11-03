import os
import subprocess

# 설정
BASE_DIR = "/root/hardway"
CERT_DIR = os.path.join(BASE_DIR, "certs")
LOG_DIR = BASE_DIR
LOG_FILE = os.path.join(LOG_DIR, "cert_generation.log")

# 클러스터 설정
KUBE_CLUSTER_NAME = "sunjae-k8s-hardway"
VIP = "172.31.1.8"  # VIP 변수
KUBE_API_SERVER_ADDRESS = VIP  # VIP 활용
KUBECTL_VERSION = "v1.29.7"

# IP 및 DNS 설정
MASTER_IPS = ["172.31.1.2", "172.31.1.3", "172.31.1.4"]
CLUSTER_IP = "10.231.0.1"  # Cluster IP
LOCAL_IP = "127.0.0.1"
SAN_IPS = MASTER_IPS + [VIP, LOCAL_IP, CLUSTER_IP]
SAN_DNS = [
    "kubernetes", "kubernetes.default", "kubernetes.default.svc", "kubernetes.default.svc.cluster.local"
]
ETCD_IPS = MASTER_IPS + [LOCAL_IP]

# 디렉토리 보장
def ensure_directories():
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

# 로그 작성
def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")
    print(message)

# 명령 실행
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_message(result.stdout.decode().strip())
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 명령 실행 실패: {command}\n{e.stderr.decode().strip()}")
        raise

# 환경변수 확인 및 설정
def ensure_environment():
    log_message("🔍 환경 변수 확인 중...")
    path_env = os.getenv("PATH", "")
    if "/usr/local/bin" not in path_env:
        log_message("⚠️ /usr/local/bin이 PATH에 포함되지 않았습니다. 설정을 추가합니다...")
        with open("/etc/profile", "a") as profile:
            profile.write("\nexport PATH=/usr/local/bin:$PATH\n")
        os.environ["PATH"] = f"/usr/local/bin:{path_env}"
        log_message("✅ /usr/local/bin이 PATH에 추가되었습니다. 새로운 쉘에서 적용됩니다.")
    else:
        log_message("✅ 환경 변수 설정이 올바르게 구성되었습니다.")

# bastion 초기 세팅
def bastion_initial_setup():
    log_message("🛠️ Bastion 초기 세팅 시작...")
    commands = [
        "apt update -y",
        "apt upgrade -y",
        "apt install net-tools htop vim openssl ipset python3-pip -y",
        "pip install scp paramiko"
    ]
    for command in commands:
        log_message(f"실행 중: {command}")
        run_command(command)
    log_message("✅ Bastion 초기 세팅 완료")

# kubectl 확인 및 설치
def ensure_kubectl():
    log_message("🔍 kubectl 확인 중...")
    try:
        result = subprocess.run(["kubectl", "version", "--client", "--short"], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
        log_message(f"✅ kubectl 설치 확인: {result.stdout.decode().strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_message("⚠️ kubectl이 설치되지 않았습니다. 다운로드를 시작합니다...")
        commands = [
            f"wget -q --show-progress --https-only --timestamping https://storage.googleapis.com/kubernetes-release/release/{KUBECTL_VERSION}/bin/linux/amd64/kubectl",
            "chmod +x kubectl",
            "mv kubectl /usr/local/bin/"
        ]
        for command in commands:
            run_command(command)
        log_message("✅ kubectl 설치 완료")

# 인증서 생성
def generate_certificates():
    log_message("🔨 인증서 생성 시작...")
    cert_commands = [
        f"openssl genrsa -out {CERT_DIR}/ca.key 2048",
        f"openssl req -new -key {CERT_DIR}/ca.key -subj '/CN=KUBERNETES-CA' -out {CERT_DIR}/ca.csr",
        f"openssl x509 -req -in {CERT_DIR}/ca.csr -signkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/ca.crt -days 3650",

        f"openssl genrsa -out {CERT_DIR}/admin.key 2048",
        f"openssl req -new -key {CERT_DIR}/admin.key -subj '/CN=admin/O=system:masters' -out {CERT_DIR}/admin.csr",
        f"openssl x509 -req -in {CERT_DIR}/admin.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/admin.crt -days 365",

        f"openssl genrsa -out {CERT_DIR}/kube-controller-manager.key 2048",
        f"openssl req -new -key {CERT_DIR}/kube-controller-manager.key -subj '/CN=system:kube-controller-manager' -out {CERT_DIR}/kube-controller-manager.csr",
        f"openssl x509 -req -in {CERT_DIR}/kube-controller-manager.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/kube-controller-manager.crt -days 365",

        f"openssl genrsa -out {CERT_DIR}/kube-scheduler.key 2048",
        f"openssl req -new -key {CERT_DIR}/kube-scheduler.key -subj '/CN=system:kube-scheduler' -out {CERT_DIR}/kube-scheduler.csr",
        f"openssl x509 -req -in {CERT_DIR}/kube-scheduler.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/kube-scheduler.crt -days 365",

        f"openssl genrsa -out {CERT_DIR}/kube-proxy.key 2048",
        f"openssl req -new -key {CERT_DIR}/kube-proxy.key -subj '/CN=system:kube-proxy' -out {CERT_DIR}/kube-proxy.csr",
        f"openssl x509 -req -in {CERT_DIR}/kube-proxy.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/kube-proxy.crt -days 365",

        f"openssl genrsa -out {CERT_DIR}/service-account.key 2048",
        f"openssl req -new -key {CERT_DIR}/service-account.key -subj '/CN=service-accounts' -out {CERT_DIR}/service-account.csr",
        f"openssl x509 -req -in {CERT_DIR}/service-account.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/service-account.crt -days 365",
    ]
    for command in cert_commands:
        log_message(f"실행 중: {command}")
        run_command(command)
    log_message("✅ 인증서 생성 완료")

# SAN 인증서 생성
def generate_san_certificates():
    log_message("🔨 SAN 인증서 생성 시작...")
    kube_apiserver_config = os.path.join(CERT_DIR, "openssl-kube-apiserver.cnf")
    with open(kube_apiserver_config, "w") as f:
        f.write("[req]\n")
        f.write("req_extensions = v3_req\n")
        f.write("distinguished_name = req_distinguished_name\n")
        f.write("\n[req_distinguished_name]\n")
        f.write("\n[v3_req]\n")
        f.write("basicConstraints = CA:FALSE\n")
        f.write("keyUsage = nonRepudiation, digitalSignature, keyEncipherment\n")
        f.write("subjectAltName = @alt_names\n")
        f.write("\n[alt_names]\n")
        for i, dns in enumerate(SAN_DNS, start=1):
            f.write(f"DNS.{i} = {dns}\n")
        for i, ip in enumerate(SAN_IPS, start=len(SAN_DNS) + 1):
            f.write(f"IP.{i} = {ip}\n")
    commands = [
        f"openssl genrsa -out {CERT_DIR}/kube-apiserver.key 2048",
        f"openssl req -new -key {CERT_DIR}/kube-apiserver.key -subj '/CN=kube-apiserver' -out {CERT_DIR}/kube-apiserver.csr -config {kube_apiserver_config}",
        f"openssl x509 -req -in {CERT_DIR}/kube-apiserver.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/kube-apiserver.crt -extensions v3_req -extfile {kube_apiserver_config} -days 365"
    ]
    for command in commands:
        log_message(f"실행 중: {command}")
        run_command(command)
    log_message("✅ SAN 인증서 생성 완료")

# etcd 인증서 생성
def generate_etcd_certificates():
    log_message("🔨 etcd 인증서 생성 시작...")
    etcd_config = os.path.join(CERT_DIR, "openssl-etcd.cnf")
    with open(etcd_config, "w") as f:
        f.write("[req]\n")
        f.write("req_extensions = v3_req\n")
        f.write("distinguished_name = req_distinguished_name\n")
        f.write("\n[req_distinguished_name]\n")
        f.write("\n[v3_req]\n")
        f.write("basicConstraints = CA:FALSE\n")
        f.write("keyUsage = nonRepudiation, digitalSignature, keyEncipherment\n")
        f.write("subjectAltName = @alt_names\n")
        f.write("\n[alt_names]\n")
        for i, ip in enumerate(ETCD_IPS, start=1):
            f.write(f"IP.{i} = {ip}\n")
    commands = [
        f"openssl genrsa -out {CERT_DIR}/etcd-server.key 2048",
        f"openssl req -new -key {CERT_DIR}/etcd-server.key -subj '/CN=etcd-server' -out {CERT_DIR}/etcd-server.csr -config {etcd_config}",
        f"openssl x509 -req -in {CERT_DIR}/etcd-server.csr -CA {CERT_DIR}/ca.crt -CAkey {CERT_DIR}/ca.key -CAcreateserial -out {CERT_DIR}/etcd-server.crt -extensions v3_req -extfile {etcd_config} -days 3650"
    ]
    for command in commands:
        log_message(f"실행 중: {command}")
        run_command(command)
    log_message("✅ etcd 인증서 생성 완료")

# kubeconfig 생성
def create_kubeconfigs():
    log_message("🔧 kubeconfig 파일 생성 시작...")
    configs = [
        {
            "name": "admin.kubeconfig",
            "user": "admin",
            "cert": "admin.crt",
            "key": "admin.key",
        },
        {
            "name": "kube-controller-manager.kubeconfig",
            "user": "system:kube-controller-manager",
            "cert": "kube-controller-manager.crt",
            "key": "kube-controller-manager.key",
        },
        {
            "name": "kube-scheduler.kubeconfig",
            "user": "system:kube-scheduler",
            "cert": "kube-scheduler.crt",
            "key": "kube-scheduler.key",
        },
        {
            "name": "kube-proxy.kubeconfig",
            "user": "system:kube-proxy",
            "cert": "kube-proxy.crt",
            "key": "kube-proxy.key",
        },
    ]
    for config in configs:
        commands = [
            f"kubectl config set-cluster {KUBE_CLUSTER_NAME} --certificate-authority={CERT_DIR}/ca.crt --embed-certs=true --server=https://{KUBE_API_SERVER_ADDRESS}:6443 --kubeconfig={CERT_DIR}/{config['name']}",
            f"kubectl config set-credentials {config['user']} --client-certificate={CERT_DIR}/{config['cert']} --client-key={CERT_DIR}/{config['key']} --embed-certs=true --kubeconfig={CERT_DIR}/{config['name']}",
            f"kubectl config set-context default --cluster={KUBE_CLUSTER_NAME} --user={config['user']} --kubeconfig={CERT_DIR}/{config['name']}",
            f"kubectl config use-context default --kubeconfig={CERT_DIR}/{config['name']}"
        ]
        for command in commands:
            log_message(f"실행 중: {command}")
            run_command(command)

    # admin.kubeconfig 복사
    admin_kubeconfig_path = os.path.join(CERT_DIR, "admin.kubeconfig")
    kube_config_path = "/root/.kube/config"
    try:
        os.makedirs("/root/.kube", exist_ok=True)
        run_command(f"cp {admin_kubeconfig_path} {kube_config_path}")
        log_message(f"✅ admin.kubeconfig 파일이 {kube_config_path}로 복사되었습니다.")
    except Exception as e:
        log_message(f"❌ admin.kubeconfig 파일 복사 실패: {str(e)}")

    log_message("✅ kubeconfig 생성 완료")

# 메인 함수
def main():
    ensure_directories()
    bastion_initial_setup()
    ensure_environment()
    log_message("=== 스크립트 시작 ===")
    ensure_kubectl()
    generate_certificates()
    generate_san_certificates()
    generate_etcd_certificates()
    create_kubeconfigs()
    log_message("=== 모든 작업 완료 ===")

if __name__ == "__main__":
    main()
