#!/usr/bin/env python3
"""ロゴのPNG（透過）の輪郭をたどって、SVG（ベクター）に変換する。標準ライブラリのみ。

使い方: python3 tools/trace_logo.py
  src/static/assets/img/renew-logo-black.png を読み、
  renew-logo-black.svg を同じフォルダに書き出す（白いロゴは、CSSで黒を白に反転して使う）。

方法:
  1. PNGを自前で読み、透明度(0〜1)の2次元配列にする
  2. 透明度0.5の等高線を「マーチング・スクエア」で半ピクセル精度にたどる
  3. 角（文字の角など）を検出して分け、なめらかな部分をベジェ曲線に当てはめる
元がラスター（600px幅）なので、元データ（Illustrator等）の完全な再現ではない。
お店から元のベクターデータを受け取れたら、そちらに差し替えるのが理想。
"""
import math
import struct
import sys
import zlib
from pathlib import Path

IMG = Path(__file__).resolve().parent.parent / "src" / "static" / "assets" / "img"


def read_alpha(path):
    d = Path(path).read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat = 8, b""
    while pos < len(d):
        n, t = struct.unpack(">I4s", d[pos:pos + 8])
        body = d[pos + 8:pos + 8 + n]
        if t == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
            assert (bd, ct, il) == (8, 6, 0), "8bit RGBA 非インターレースのみ対応"
        elif t == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    bpp, stride = 4, w * 4
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = cur[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                cur[i] = (cur[i] + a) & 255
            elif f == 2:
                cur[i] = (cur[i] + b) & 255
            elif f == 3:
                cur[i] = (cur[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 255
        rows.append(cur)
        prev = cur
    return w, h, [[rows[y][x * 4 + 3] / 255.0 for x in range(w)] for y in range(h)]


def contours(w, h, a, t=0.5):
    """マーチング・スクエアで、透明度tの等高線を閉じた折れ線(頂点列)として返す。"""
    P = 1  # 周囲に1ピクセルの余白（図形が端に接しても閉じるように）
    W, H = w + 2 * P, h + 2 * P

    def v(x, y):
        x -= P
        y -= P
        return a[y][x] if 0 <= x < w and 0 <= y < h else 0.0

    pos = {}   # 辺キー -> 座標
    adj = {}   # 辺キー -> つながる辺キー

    def link(k1, p1, k2, p2):
        pos[k1], pos[k2] = p1, p2
        adj.setdefault(k1, []).append(k2)
        adj.setdefault(k2, []).append(k1)

    def interp(v0, v1):
        return (t - v0) / (v1 - v0) if v1 != v0 else 0.5

    for y in range(H - 1):
        for x in range(W - 1):
            tl, tr, br, bl = v(x, y), v(x + 1, y), v(x + 1, y + 1), v(x, y + 1)
            idx = (tl >= t) * 8 + (tr >= t) * 4 + (br >= t) * 2 + (bl >= t)
            if idx in (0, 15):
                continue
            top = (("h", x, y), (x + interp(tl, tr), y))
            right = (("v", x + 1, y), (x + 1, y + interp(tr, br)))
            bottom = (("h", x, y + 1), (x + interp(bl, br), y + 1))
            left = (("v", x, y), (x, y + interp(tl, bl)))
            segs = {1: [(left, bottom)], 2: [(bottom, right)], 3: [(left, right)], 4: [(top, right)],
                    6: [(top, bottom)], 7: [(left, top)], 8: [(left, top)], 9: [(top, bottom)],
                    11: [(top, right)], 12: [(left, right)], 13: [(bottom, right)], 14: [(left, bottom)]}
            if idx == 5 or idx == 10:  # 鞍点：中心の値で判定
                c = (tl + tr + br + bl) / 4
                if (idx == 5) == (c >= t):
                    segs[idx] = [(left, top), (bottom, right)]
                else:
                    segs[idx] = [(left, bottom), (top, right)]
            for s1, s2 in segs[idx]:
                link(s1[0], s1[1], s2[0], s2[1])
    seen, loops = set(), []
    for k in list(adj):
        if k in seen:
            continue
        loop, cur, prev = [], k, None
        while cur not in seen:
            seen.add(cur)
            loop.append(pos[cur])
            nxt = [n for n in adj[cur] if n != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
        if len(loop) > 3:
            # 格子の点は画素の中心(x+0.5, y+0.5)にあたる。余白ぶんを戻して画像の座標にする
            loops.append([(px - P + 0.5, py - P + 0.5) for px, py in loop])
    return loops


def dp(pts, eps):
    """Douglas-Peucker（開いた折れ線の間引き）"""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    best, bi = -1, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
        if d > best:
            best, bi = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return dp(pts[:bi + 1], eps)[:-1] + dp(pts[bi:], eps)


def corner_flags(pts, k=4, thr=math.radians(50)):
    n = len(pts)
    ang = []
    for i in range(n):
        ax, ay = pts[i][0] - pts[(i - k) % n][0], pts[i][1] - pts[(i - k) % n][1]
        bx, by = pts[(i + k) % n][0] - pts[i][0], pts[(i + k) % n][1] - pts[i][1]
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la == 0 or lb == 0:
            ang.append(0)
            continue
        c = max(-1, min(1, (ax * bx + ay * by) / (la * lb)))
        ang.append(math.acos(c))
    flags = []
    for i in range(n):
        if ang[i] < thr:
            flags.append(False)
            continue
        flags.append(all(ang[i] >= ang[(i + j) % n] for j in range(-k, k + 1) if j))
    return flags


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def run_to_path(run, first):
    """角から角までの1本の線を、直線かベジェ曲線で表す。"""
    pts = dp(run, 0.22)
    out = ""
    if first:
        out += f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"
    if len(pts) == 2:
        return out + f"L{fmt(pts[1][0])} {fmt(pts[1][1])}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out += f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
    return out


def loop_to_path(pts):
    flags = corner_flags(pts)
    corners = [i for i, f in enumerate(flags) if f]
    n = len(pts)
    if not corners:  # 角のないなめらかな輪（Oの内側など）
        base = pts[:: max(1, n // 40)]
        base = base + [base[0]]
        d = f"M{fmt(base[0][0])} {fmt(base[0][1])}"
        m = len(base) - 1
        for i in range(m):
            p0, p1, p2, p3 = base[(i - 1) % m], base[i], base[(i + 1) % m], base[(i + 2) % m]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d += f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
        return d + "Z"
    rot = pts[corners[0]:] + pts[:corners[0]]
    cs = [(c - corners[0]) % n for c in corners]
    d = ""
    for j, c in enumerate(cs):
        end = cs[j + 1] if j + 1 < len(cs) else n
        run = rot[c:end + 1] if end < n else rot[c:] + [rot[0]]
        d += run_to_path(run, first=(j == 0))
    return d + "Z"


def main():
    w, h, a = read_alpha(IMG / "renew-logo-black.png")
    paths = [loop_to_path(lp) for lp in contours(w, h, a)]
    d = "".join(paths)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="ReNEW.">'
           f'<path fill="#000" fill-rule="evenodd" d="{d}"/></svg>\n')
    (IMG / "renew-logo-black.svg").write_text(svg, encoding="utf-8")
    print(f"{len(paths)} 本の輪郭 / {len(d)} 文字のパス → renew-logo-black.svg")


if __name__ == "__main__":
    sys.exit(main())
