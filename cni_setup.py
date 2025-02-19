import os
import subprocess
import time

# 설정
HELM_VERSION = "v3.9.4"
HELM_URL = f"https://get.helm.sh/helm-{HELM_VERSION}-linux-amd64.tar.gz"
HELM_BINARY = "/usr/bin/helm"
CILIUM_VERSION = "1.15.4"
CNI_NAMESPACE = "kube-system"
LOG_FILE = "/root/bastion_setup.log"

# 로그 작성 함수
def log_message(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} - {message}\n")
    print(message)

# 명령 실행 함수
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_message(result.stdout.decode().strip())
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 명령 실행 실패: {command}\n{e.stderr.decode().strip()}")
        raise

# Helm 설치 함수
def install_helm():
    log_message("🔄 Helm 설치 중...")
    helm_tarball = "/tmp/helm.tar.gz"
    if not os.path.exists(HELM_BINARY):
        run_command(f"wget -q -O {helm_tarball} {HELM_URL}")
        run_command(f"tar -xvf {helm_tarball} -C /tmp")
        run_command(f"mv /tmp/linux-amd64/helm {HELM_BINARY}")
        log_message("✅ Helm 설치 완료")
    else:
        log_message("✅ Helm이 이미 설치되어 있습니다.")

# Cilium 설치 함수
def install_cilium():
    log_message("🔄 Cilium 설치 중...")
    run_command(f"helm repo add cilium https://helm.cilium.io")
    run_command(f"helm repo update")
    run_command(f"helm install cilium cilium/cilium --version {CILIUM_VERSION} --namespace {CNI_NAMESPACE} --create-namespace")
    log_message("✅ Cilium 설치 완료")

# RBAC 설정 함수
def setup_rbac():
    log_message("🔄 RBAC 설정 중...")
    cluster_role_yaml = "/tmp/kubelet-clusterrole.yaml"
    cluster_role_binding_yaml = "/tmp/kubelet-clusterrolebinding.yaml"

    cluster_role_content = """
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: system:kube-apiserver-to-kubelet
rules:
- apiGroups:
  - ""
  resources:
    - nodes/proxy
    - nodes/stats
    - nodes/log
    - nodes/spec
    - nodes/metrics
  verbs:
    - "*"
"""
    cluster_role_binding_content = """
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: system:kube-apiserver
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:kube-apiserver-to-kubelet
subjects:
  - kind: User
    name: kube-apiserver
    apiGroup: rbac.authorization.k8s.io
"""

    with open(cluster_role_yaml, "w") as f:
        f.write(cluster_role_content.strip())
    with open(cluster_role_binding_yaml, "w") as f:
        f.write(cluster_role_binding_content.strip())

    run_command(f"kubectl apply -f {cluster_role_yaml}")
    run_command(f"kubectl apply -f {cluster_role_binding_yaml}")
    log_message("✅ RBAC 설정 완료")

# CoreDNS 배포 함수
def deploy_coredns():
    log_message("🔄 CoreDNS 배포 중...")
    coredns_yaml = "/tmp/coredns.yaml"
    coredns_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
            lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf {
          prefer_udp
        }
        cache 30
        loop
        reload
        loadbalance
    }
"""
    with open(coredns_yaml, "w") as f:
        f.write(coredns_content.strip())

    run_command(f"kubectl apply -f {coredns_yaml}")
    log_message("✅ CoreDNS 배포 완료")

# Netshoot 배포 함수
def deploy_netshoot():
    log_message("🔄 Netshoot 배포 중...")
    netshoot_yaml = "/tmp/netshoot.yaml"
    netshoot_content = """
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: netshoot-cluster
  labels:
    app: netshoot-cluster
spec:
  selector:
    matchLabels:
      name: netshoot-cluster
  template:
    metadata:
      labels:
        name: netshoot-cluster
    spec:
      containers:
      - name: netshoot-cluster
        image: nicolaka/netshoot
        tty: true
        stdin: true
"""
    with open(netshoot_yaml, "w") as f:
        f.write(netshoot_content.strip())

    run_command(f"kubectl apply -f {netshoot_yaml}")
    log_message("✅ Netshoot 배포 완료")

# 서비스 상태 확인 함수
def verify_services():
    log_message("🔄 서비스 상태 확인 중...")
    run_command("kubectl get pods -n kube-system")
    run_command("kubectl get svc -n kube-system")
    log_message("✅ 서비스 상태 확인 완료")

# 메인 함수
def main():
    log_message("=== Bastion 노드 Cilium 및 네트워크 설정 시작 ===")
    install_helm()
    install_cilium()
    setup_rbac()
    deploy_coredns()
    deploy_netshoot()
    verify_services()
    log_message("=== Bastion 노드 설정 완료 ===")

if __name__ == "__main__":
    main()
