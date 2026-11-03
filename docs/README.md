# Kubernetes Hard Way HA 설치 가이드

![Kubernetes The Hard Way 배너](images/00-banner.png)

kubeadm 없이 바이너리와 systemd 유닛으로 Kubernetes v1.29.7 클러스터(master 3 / worker 3, etcd 3노드, Pacemaker+Corosync VIP, Cilium v1.15.4)를 VMware 랩에 직접 구축한 과정을 정리한 문서입니다. 저장소 루트의 Python 스크립트는 이 수동 절차를 자동화한 것입니다.

> [!NOTE]
> 공개용으로 정리하면서 비밀번호, 개인 키, bootstrap token 값은 자리표시자로 바꾸거나 생략했습니다. 사설 대역 IP(`172.31.1.0/24`, `192.168.34.0/24`)는 랩 값을 그대로 두었습니다.

## 목차

- [01. 개요: 환경, VM 구성, 인증서·포트](01-overview.md)
- [02. Bastion과 노드 네트워크 구성](02-bastion-network.md)
- [03. CA와 컴포넌트 클라이언트 인증서](03-certificates.md)
- [04. kubeconfig 생성](04-kubeconfig.md)
- [05. API 서버·etcd 인증서와 Service Account 키](05-apiserver-etcd-sa-certs.md)
- [06. 인증서·kubeconfig 배포](06-distribute-certs.md)
- [07. etcd 클러스터 구성](07-etcd.md)
- [08. 컨트롤 플레인 부트스트랩](08-control-plane.md)
- [09. Worker01 구성 (수동 인증서)](09-worker01.md)
- [10. Cilium CNI, RBAC, CoreDNS](10-cilium-coredns.md)
- [11. 네트워크 통신 테스트 (netshoot, echo, IPVS)](11-network-test.md)
- [12. TLS Bootstrapping으로 Worker02·03 조인](12-tls-bootstrap-workers.md)

## 랩 토폴로지 요약

| 역할 | 호스트 | IP |
|---|---|---|
| Bastion (TLS·kubectl·NAT) | bastion | 192.168.34.226 / 172.31.1.1 |
| Control Plane | k8s-hardway-master01~03 | 172.31.1.2 ~ 172.31.1.4 |
| API VIP (Pacemaker) | - | 172.31.1.8 |
| Worker | k8s-hardway-worker01~03 | 172.31.1.5 ~ 172.31.1.7 |

| 항목 | 값 |
|---|---|
| Service CIDR | 10.231.0.0/18 |
| Pod CIDR | 10.240.0.0/13 |
| Cluster DNS | 10.231.0.10 |
