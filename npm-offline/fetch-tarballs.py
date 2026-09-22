#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch-tarballs.py — 按 missing-npm-tarballs.txt 下载全部 npm tarball 并逐个校验 sha512。

跨平台版本（Windows / macOS / Linux 都能跑，只用标准库），是 fetch-tarballs.ps1 的等价物。
PowerShell 版仍在同目录，二选一即可。

用法（在本目录下执行）:
    python fetch-tarballs.py                       # 默认：镜像 registry.npmmirror.com → 官方 registry.npmjs.org 直连
    python fetch-tarballs.py --proxy http://127.0.0.1:7897   # 追加"走代理访问 npmjs"作为兜底
    python fetch-tarballs.py --no-mirror           # 只走官方源

产物:
    tarballs/<registry 原始路径>      —— 例如 tarballs/@babel/code-frame/-/code-frame-8.0.0.tgz
    results.tsv                       —— 每个包的来源 / 字节数 / 失败原因，可用来核对
末尾打印 verified: N / M；有 FAILED 时重跑本脚本即可补齐（已校验过的文件会跳过）。

注意：必须下载 registry 上的**原始发布版** tarball。`npm pack` 重新打包出来的字节不同、
sha512 与 package-lock.json 里的 integrity 不匹配，`npm ci` 会拒绝安装。
"""
import argparse, base64, hashlib, json, os, sys, threading, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
NPMJS = "https://registry.npmjs.org/"
lock = threading.Lock()
done = 0


def sha512_b64(path):
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def opener(proxy):
    if not proxy:
        return urllib.request.build_opener()
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )


def download(url, dest, op, timeout=180):
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "fetch-tarballs/1.0"})
    with op.open(req, timeout=timeout) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=os.path.join(HERE, "missing-npm-tarballs.txt"))
    ap.add_argument("--out", default=os.path.join(HERE, "tarballs"))
    ap.add_argument("--registry", default="https://registry.npmmirror.com",
                    help="清单 URL 会被改写到这个镜像；空字符串表示不改写")
    ap.add_argument("--proxy", default=os.environ.get("HTTP_PROXY") or "",
                    help="兜底用的 HTTP(S) 代理，例：http://127.0.0.1:7897")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--no-mirror", action="store_true", help="只用清单里的官方 URL")
    args = ap.parse_args()

    rows = []
    with open(args.list, "r", encoding="utf-8") as f:
        for line in f:                      # 自动兼容 LF / CRLF 清单
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                print("BAD LINE: " + line[:80], flush=True)
                continue
            rows.append((parts[0], parts[1], parts[2]))

    op_direct, op_proxy = opener(None), opener(args.proxy)
    print("list=%d out=%s jobs=%d proxy=%s" % (len(rows), args.out, args.jobs, args.proxy or "-"),
          flush=True)

    results = []

    def work(item):
        global done
        name, url, integrity = item
        rel = url.split("://", 1)[1].split("/", 1)[1]      # 去掉主机名，保留 registry 路径
        dest = os.path.join(args.out, *rel.split("/"))
        want = integrity.split("-", 1)[1]
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if os.path.isfile(dest):                            # 断点续跑：已校验过的直接跳过
            try:
                if sha512_b64(dest) == want:
                    with lock:
                        done += 1
                    return (name, "cached", os.path.getsize(dest), "")
            except OSError:
                pass

        mirror = url.replace(NPMJS, args.registry.rstrip("/") + "/") if args.registry else url
        attempts = []
        if mirror != url and not args.no_mirror:
            attempts.append(("mirror", mirror, op_direct))
        attempts.append(("npmjs", url, op_direct))
        if args.proxy:
            attempts.append(("npmjs-proxy", url, op_proxy))

        last = ""
        for label, u, o in attempts:
            for _ in (1, 2):
                try:
                    download(u, dest, o)
                    if sha512_b64(dest) == want:
                        with lock:
                            done += 1
                        return (name, "ok:" + label, os.path.getsize(dest), "")
                    last = "integrity mismatch via " + label
                    os.remove(dest)
                except Exception as e:                      # noqa: BLE001
                    last = "%s: %s %s" % (label, type(e).__name__, e)
                    time.sleep(1.5)
        return (name, "FAILED", 0, last)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for i, res in enumerate(ex.map(work, rows), 1):
            results.append(res)
            if res[1] == "FAILED":
                print("[%d/%d] FAILED %s — %s" % (i, len(rows), res[0], res[3]), flush=True)
            elif i % 25 == 0:
                print("[%d/%d] verified=%d elapsed=%.0fs" % (i, len(rows), done, time.time() - t0),
                      flush=True)

    ok = sum(1 for r in results if r[1] != "FAILED")
    failed = [r for r in results if r[1] == "FAILED"]
    report = os.path.join(os.path.dirname(os.path.abspath(args.out)), "results.tsv")
    with open(report, "w", encoding="utf-8", newline="\n") as f:
        f.write("package\tsource\tbytes\tnote\n")
        for r in sorted(results):
            f.write("%s\t%s\t%d\t%s\n" % r)
    srcs = {}
    for r in results:
        srcs[r[1]] = srcs.get(r[1], 0) + 1
    print(json.dumps({"verified": ok, "lines": len(rows), "bytes": sum(r[2] for r in results),
                      "elapsed_s": round(time.time() - t0, 1), "sources": srcs,
                      "failed": [r[0] for r in failed]}, ensure_ascii=False), flush=True)
    print("verified: %d / %d" % (ok, len(rows)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
