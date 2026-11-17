"""スマホからカメラ / Web Bluetooth を使うための HTTPS サーバ（自己署名証明書）。

    python3 scripts/serve_https.py [port]

表示された https://<PC の IP>:<port>/docs/camera.html を同じ Wi-Fi のスマホで開く。
証明書の警告が出たら「詳細設定 → アクセスする」で進む。
"""
import http.server, os, socket, ssl, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_DIR = os.path.join(ROOT, 'scripts', 'cert')
CERT, KEY = os.path.join(CERT_DIR, 'cert.pem'), os.path.join(CERT_DIR, 'key.pem')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8443


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))  # 実際には送信しない（経路の決定だけ）
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


ip = lan_ip()
if not os.path.exists(CERT):
    os.makedirs(CERT_DIR, exist_ok=True)
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '365',
                    '-keyout', KEY, '-out', CERT, '-subj', '/CN=jump-local',
                    '-addext', f'subjectAltName=IP:{ip},DNS:localhost'], check=True)

os.chdir(ROOT)
httpd = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), http.server.SimpleHTTPRequestHandler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(CERT, KEY)
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
print(f'スマホで開く: https://{ip}:{PORT}/docs/camera.html')
print(f'PC で開く   : https://localhost:{PORT}/docs/camera.html  （または http サーバで http://localhost/...）')
httpd.serve_forever()
