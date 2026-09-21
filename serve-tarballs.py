"""把 fetch-tarballs.ps1 产出的 tarballs/ 当成本地 npm registry 起一个静态服务。
（Hermes 这边收到文件后由我来跑；放在仓库里只是为了让流程透明。）
用法: python serve-tarballs.py [port]   # 默认 4873
"""
import functools, http.server, os, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarballs")
port = int(sys.argv[1]) if len(sys.argv) > 1 else 4873
if not os.path.isdir(root):
    sys.exit(f"missing tarball dir: {root}")
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
print(f"serving {root} on http://127.0.0.1:{port}", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
