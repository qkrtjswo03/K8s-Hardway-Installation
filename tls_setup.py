import subprocess
import time


# 로그 작성 함수
def log_message(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_file = "/root/tls_bootstrapping_setup.log"
    with open(log_file, "a", encoding="utf-8") as log:
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


def create_bootstrap_token():
    log_message("🔄 Bootstrap Token 생성 중...")
    bootstrap_token_yaml = """apiVersion: v1
kind: Secret
metadata:
  name: bootstrap-token-CHANGE_ME_TOKEN_ID
  namespace: kube-system
type: bootstrap.kubernetes.io/token
stringData:
  description: "Bootstrap token for worker nodes"
  token-id: CHANGE_ME_TOKEN_ID
  token-secret: CHANGE_ME_BOOTSTRAP_TOKEN_SECRET
  usage-bootstrap-authentication: "true"
  usage-bootstrap-signing: "true"
  auth-extra-groups: system:bootstrappers:worker
"""
    with open("/root/bootstrap-token-CHANGE_ME_TOKEN_ID.yaml", "w") as f:
        f.write(bootstrap_token_yaml)

    run_command("kubectl apply -f /root/bootstrap-token-CHANGE_ME_TOKEN_ID.yaml")
    log_message("✅ Bootstrap Token 생성 완료")


def create_rbac_for_bootstrapping():
    log_message("🔄 RBAC 설정 생성 중...")

    # ClusterRoleBinding: create-csrs-for-bootstrapping.yaml
    csrs_yaml = """kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: create-csrs-for-bootstrapping
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:node-bootstrapper
  apiGroup: rbac.authorization.k8s.io
"""
    with open("/root/csrs-for-bootstrapping.yaml", "w") as f:
        f.write(csrs_yaml)

    # ClusterRoleBinding: auto-approve-csrs-for-group.yaml
    auto_approve_yaml = """kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: auto-approve-csrs-for-group
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:nodeclient
  apiGroup: rbac.authorization.k8s.io
"""
    with open("/root/auto-approve-csrs-for-group.yaml", "w") as f:
        f.write(auto_approve_yaml)

    # Apply the RBAC YAMLs
    run_command("kubectl apply -f /root/csrs-for-bootstrapping.yaml")
    run_command("kubectl apply -f /root/auto-approve-csrs-for-group.yaml")
    log_message("✅ RBAC 설정 생성 완료")


def main():
    log_message("=== TLS Bootstrapping 설정 시작 ===")
    create_bootstrap_token()
    create_rbac_for_bootstrapping()
    log_message("=== TLS Bootstrapping 설정 완료 ===")


if __name__ == "__main__":
    main()
