#!/usr/bin/env python3
"""Instagram の最新投稿を取得し、TOPのタイル表示用の画像と一覧(JSON)を作る。

- 環境変数 IG_ACCESS_TOKEN（長期アクセストークン）が無いときは何もしない（手動で置いた画像のまま）。
- どこかで失敗したときも、既存の画像・一覧には触らずに正常終了する（サイトは壊れない）。
- 実行のたびにトークンの有効期限を延ばす（約60日 → 毎日実行していれば切れない）。
- 取得した画像は src/static/assets/img/instagram/ に保存し、src/instagram_posts.json に一覧を書く。
  build.py はこの JSON があればそれを使い、無ければ build.py 内の INSTAGRAM_POSTS を使う。
標準ライブラリのみ。ローカルでも GitHub Actions でも動く。
"""
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
IMG_DIR = SRC / "static" / "assets" / "img" / "instagram"
JSON_OUT = SRC / "instagram_posts.json"
BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
WANT = 6


def log(msg):
    print(f"[instagram] {msg}", flush=True)


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "renew-site-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else json.loads(data.decode("utf-8"))


def refresh_token():
    """有効期限を延ばす。失敗しても取得は続ける。"""
    try:
        q = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": TOKEN})
        res = get(f"{BASE}/refresh_access_token?{q}")
        days = int(res.get("expires_in", 0)) // 86400
        log(f"トークンを更新しました（残り約{days}日）")
        if res.get("access_token") and res["access_token"] != TOKEN:
            log("::warning::新しいトークンが発行されました。GitHub の Secret IG_ACCESS_TOKEN を新しい値に差し替えてください。")
    except Exception as e:  # noqa: BLE001
        log(f"::warning::トークンの更新に失敗しました（取得は続けます）: {e}")


def make_alt(caption):
    line = (caption or "").strip().splitlines()[0] if (caption or "").strip() else ""
    line = re.sub(r"[#＃]\S+", "", line).strip()
    line = re.sub(r"\s+", " ", line)
    if len(line) > 40:
        line = line[:40] + "…"
    return f"Instagramの投稿：{line}" if line else "Instagramの最新の投稿"


def main():
    if not TOKEN:
        log("IG_ACCESS_TOKEN が未設定のため、取得をスキップします（手動で置いた画像のまま）。")
        return 0
    refresh_token()
    try:
        q = urllib.parse.urlencode({
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink",
            "limit": 24,
            "access_token": TOKEN,
        })
        media = get(f"{BASE}/me/media?{q}").get("data", [])
    except Exception as e:  # noqa: BLE001
        log(f"::warning::投稿の取得に失敗しました。今の画像のままにします: {e}")
        return 0

    picks = []
    for m in media:
        t = m.get("media_type")
        url = m.get("thumbnail_url") if t == "VIDEO" else m.get("media_url")
        if url and t in ("IMAGE", "CAROUSEL_ALBUM", "VIDEO"):
            picks.append((url, make_alt(m.get("caption")), m.get("permalink")))
    picks = picks[:WANT]
    picks = picks[: (len(picks) // 3) * 3]  # 3列グリッドなので3の倍数にそろえる
    if len(picks) < 3:
        log("::warning::使える投稿が3件未満のため、今の画像のままにします。")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, (url, alt, link) in enumerate(picks, 1):
            try:
                data = get(url, binary=True)
            except Exception as e:  # noqa: BLE001
                log(f"::warning::画像{i}の取得に失敗したため、今の画像のままにします: {e}")
                return 0
            if data[:3] != b"\xff\xd8\xff" or len(data) < 5000:
                log(f"::warning::画像{i}がJPEGとして不正なため、今の画像のままにします。")
                return 0
            name = f"insta-{i:02d}.jpg"
            (Path(tmp) / name).write_bytes(data)
            files.append((name, alt, link))
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        for name, _, _ in files:
            (IMG_DIR / name).write_bytes((Path(tmp) / name).read_bytes())
    JSON_OUT.write_text(json.dumps([list(f) for f in files], ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"最新の投稿{len(files)}件を取得しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
