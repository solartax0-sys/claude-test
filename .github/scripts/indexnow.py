"""배포 후 빙(인덱스나우)에 새로 바뀐 페이지 주소를 알린다.
ALL=1 이면 sitemap.xml 의 모든 주소를 보낸다."""
import json, os, re, subprocess, sys, urllib.request, glob

HOST = "solartax.kr"
key_files = [f for f in glob.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", f)]
if not key_files:
    sys.exit("인덱스나우 키 파일 없음")
KEY = key_files[0][:-4]

def to_url(path):
    if path == "index.html":
        return f"https://{HOST}/"
    if path.endswith("/index.html"):
        return f"https://{HOST}/{path[:-10]}"
    return f"https://{HOST}/{path}"

if os.environ.get("ALL") == "1":
    urls = re.findall(r"<loc>([^<]+)</loc>", open("sitemap.xml", encoding="utf-8").read())
else:
    before = os.environ.get("BEFORE", "")
    if not before or set(before) == {"0"}:
        before = "HEAD~1"
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=AM", before, "HEAD"], text=True)
    except subprocess.CalledProcessError:
        out = ""
    paths = [p for p in out.split() if p.endswith(".html")
             and not p.startswith((".github/", "admin/"))]
    urls = [to_url(p) for p in paths]
    if paths:
        urls.append(f"https://{HOST}/")

urls = sorted(set(urls))
if not urls:
    print("알릴 주소 없음")
    sys.exit(0)

body = json.dumps({"host": HOST, "key": KEY,
                   "keyLocation": f"https://{HOST}/{KEY}.txt",
                   "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("인덱스나우 응답", r.status, "주소", len(urls), "개")
except urllib.error.HTTPError as e:
    # 실패해도 배포는 이미 끝났으므로 작업을 실패시키지 않는다
    print("인덱스나우 오류", e.code, e.read()[:300])
for u in urls:
    print(" ", u)
