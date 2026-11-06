#!/usr/bin/env python3
"""公開後の点検ツール：実際のURLにアクセスして、リダイレクト・サイトマップ・検索まわりを確認する。標準ライブラリのみ。

使い方
  python3 tools/check_launch.py                       # 本番 https://renew-souki.jp を点検
  python3 tools/check_launch.py https://example.com   # 別のURLを点検（テスト環境など）
  python3 tools/check_launch.py http://localhost:8765 --skip-redirects
                                                      # ローカル確認用（Apacheの転送は動かないので転送の点検を省く）

結果は ✅（OK）／❌（要対応）／⚠（確認してください）で表示し、❌があると終了コード1で終わる。
"""
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (ARGS[0] if ARGS else "https://renew-souki.jp").rstrip("/")
SKIP_REDIRECTS = "--skip-redirects" in sys.argv
HOST = urllib.parse.urlparse(BASE).netloc
PROD = "renew-souki.jp"

OLD_TO_NEW = {  # 旧URL（STUDIO）→ 新URL。.htaccess と同じ
    "/fullconstrution": "/menu/full/",
    "/subscription": "/menu/subscription/",
    "/qanda": "/faq/",
    "/concept": "/concept/",
    "/menu": "/menu/",
    "/contact": "/contact/",
}

results = []


def rec(ok, label, detail=""):
    mark = {True: "✅", False: "❌", None: "⚠ "}[ok]
    results.append(ok)
    print(f"{mark} {label}" + (f"  … {detail}" if detail else ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url, method="GET"):
    """(status, headers, body) を返す。転送は追いかけない。通信できないときは (0, {}, エラー文)。"""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "renew-launch-check/1.0"})
    try:
        with OPENER.open(req, timeout=25) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), (e.read().decode("utf-8", "replace") if method == "GET" else "")
    except Exception as e:  # noqa: BLE001
        return 0, {}, str(e)


def loc(h):
    return next((v for k, v in h.items() if k.lower() == "location"), "")


def check_redirects():
    print("\n■ リダイレクト")
    s, h, _ = fetch(f"http://{PROD}/")
    rec(s == 301 and loc(h) == f"https://{PROD}/", "http → https（1回の転送）", f"{s} {loc(h)}")
    s, h, _ = fetch(f"https://www.{PROD}/")
    rec(s == 301 and loc(h) == f"https://{PROD}/", "https://www → wwwなし（1回の転送）", f"{s} {loc(h)}")
    for old, new in OLD_TO_NEW.items():
        want = f"https://{PROD}{new}"
        s, h, _ = fetch(f"https://{PROD}{old}")
        rec(s == 301 and loc(h) == want, f"旧URL {old} → {new}", f"{s} {loc(h)}")
    s, h, _ = fetch(f"http://www.{PROD}/qanda")
    rec(s == 301 and loc(h) == f"https://{PROD}/faq/", "http://www の旧URLも1回で最終URLへ（例：/qanda）", f"{s} {loc(h)}")


def page_checks(paths):
    print("\n■ ページ（表示・検索まわり）")
    for p in paths:
        s, h, body = fetch(BASE + p)
        if s != 200:
            rec(False, f"{p} が表示できる", f"HTTP {s}")
            continue
        can = re.search(r'<link rel="canonical" href="([^"]+)"', body)
        noindex = re.search(r'<meta name="robots" content="[^"]*noindex', body)
        title = re.search(r"<title>(.*?)</title>", body, re.S)
        og = 'property="og:image"' in body
        canon_ok = bool(can) and urllib.parse.urlparse(can.group(1)).path == p
        probs = []
        if not canon_ok:
            probs.append("canonicalが不正")
        if noindex:
            probs.append("noindexが付いている（検索に出ません）")
        if not (title and title.group(1).strip()):
            probs.append("titleが無い")
        if not og:
            probs.append("OGP画像の指定が無い")
        rec(not probs, p, "・".join(probs))


def sitemap_checks():
    print("\n■ サイトマップ・robots")
    s, h, body = fetch(f"{BASE}/sitemap.xml")
    if s != 200:
        rec(False, "sitemap.xml が表示できる", f"HTTP {s}")
        return []
    locs = re.findall(r"<loc>([^<]+)</loc>", body)
    rec(bool(locs), f"sitemap.xml に {len(locs)} 件のURL")
    bad_host = [u for u in locs if urllib.parse.urlparse(u).netloc != PROD]
    rec(not bad_host, "sitemapのURLがすべて https://renew-souki.jp", ", ".join(bad_host[:2]))
    paths, broken = [], []
    for u in locs:
        path = urllib.parse.urlparse(u).path or "/"
        paths.append(path)
        st, _, _ = fetch(BASE + path, "HEAD")
        if st != 200:
            broken.append(f"{path}={st}")
    rec(not broken, "sitemapの全URLが 200 で表示できる", ", ".join(broken[:4]))
    s, h, rb = fetch(f"{BASE}/robots.txt")
    ok = s == 200 and re.search(r"(?im)^\s*Disallow:\s*/\s*$", rb) is None and "sitemap.xml" in rb
    rec(ok, "robots.txt が検索を許可し、sitemapを案内している", f"HTTP {s}" if s != 200 else "")
    return paths


def misc_checks():
    print("\n■ その他")
    s, h, top = fetch(BASE + "/")
    rec('name="google-site-verification"' in top, "Search Console の確認タグ（google-site-verification）がある")
    ga = re.search(r"G-[A-Z0-9]{6,}", top)
    rec(True if ga else None, "GA4 の計測タグ", ga.group(0) if ga else "未設定です（計測する場合は build.py の ga4_id を設定）")
    s, _, pv = fetch(BASE + "/privacy/")
    rec("制定日：" in pv, "プライバシーポリシーに制定日がある", "未設定です（build.py の privacy_date に公開日を入れる）" if "制定日：" not in pv else "")
    s, h, nf = fetch(BASE + "/this-page-does-not-exist-check/")
    rec(s == 404, "存在しないURLで 404 が返る", f"HTTP {s}")
    hdr = {k.lower() for k in h}
    rec("x-content-type-options" in hdr, "セキュリティヘッダーが付いている（.htaccess が効いている）")
    assets = set(re.findall(r'(?:src|href)="(/assets/[^"]+)"', top))
    broken = []
    for a in sorted(assets):
        st, _, _ = fetch(BASE + a.split("?")[0], "HEAD")
        if st != 200:
            broken.append(f"{a}={st}")
    rec(not broken, f"TOPが使う画像・CSS・JS（{len(assets)}件）がすべて読み込める", ", ".join(broken[:3]))


def main():
    print(f"点検するURL：{BASE}" + ("（転送の点検は省略）" if SKIP_REDIRECTS else ""))
    s, _, e = fetch(BASE + "/")
    if s == 0:
        print(f"❌ {BASE} に接続できません：{e}")
        return 1
    if not SKIP_REDIRECTS:
        check_redirects()
    paths = sitemap_checks()
    page_checks(sorted(set(paths or ["/"])))
    misc_checks()
    ng, warn = results.count(False), results.count(None)
    print(f"\n結果：✅ {results.count(True)} 件 / ❌ {ng} 件 / ⚠ {warn} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
