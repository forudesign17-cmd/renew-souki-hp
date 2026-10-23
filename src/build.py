#!/usr/bin/env python3
"""ReNEW. サイトのビルドスクリプト（Python 3 標準ライブラリのみ）

src/pages/ のページ本文に共通のヘッダー・フッター・CTA を組み合わせ、
public_html/ に静的HTMLを書き出す。public_html/ の中身をそのままサーバーへアップロードする。

    python3 src/build.py                    # 本番用（ルート直下に置く）
    BASE_PATH=/test python3 src/build.py    # サブディレクトリのテスト環境に置く場合

ページファイルの先頭には JSON のメタ情報をコメントで書く：
    <!--{ "title": "...", "description": "...", "breadcrumb": [["MENU", "/menu/"]] }-->
"""
import datetime
import html
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "public_html"
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
# PREVIEW=1 で全ページ noindex（GitHub Pages などの確認用。検索エンジンに載せない）
PREVIEW = os.environ.get("PREVIEW") == "1"

# ---------------------------------------------------------------------------
# サイト設定（ここを書き換えれば全ページに反映される）
# ---------------------------------------------------------------------------
SITE = {
    "url": "https://renew-souki.jp",
    "name": "ReNEW.",
    "ga4_id": "",  # 例: "G-XXXXXXXXXX"。空なら GA4 タグを出力しない
    "gsc_verification": "",  # 現行サイトの google-site-verification の値を引き継ぐ
    # サブスクの枠表示。満枠になったら None にすると「キャンセル待ち受付中」に切り替わる
    "sub_slots": "先着5台限定",
}

SNS = [  # 並び順はデザインシステム（X → Instagram → LINE → TikTok → YouTube）
    ("x", "X", "https://twitter.com/Renew_souki"),
    ("instagram", "Instagram", "https://www.instagram.com/renew.bc/"),
    ("line", "LINE", "https://line.me/R/ti/p/@701hoscx"),
    ("tiktok", "TikTok", "https://www.tiktok.com/@renew_okayama"),
    ("youtube", "YouTube", "https://www.youtube.com/@renew.0527"),
]
LINE_URL = SNS[2][2]

NAV = [  # (英字, 和文, URL, 子メニュー)
    ("HOME", "トップ", "/", []),
    ("CONCEPT", "コンセプト", "/concept/", []),
    ("MENU", "メニュー", "/menu/", [("フル施工", "/menu/full/"), ("サブスク", "/menu/subscription/"), ("個別メニュー", "/menu/option/")]),
    ("WORKS", "施工事例", "/works/", []),
    ("FLOW", "ご依頼の流れ", "/flow/", []),
    ("FAQ", "よくあるご質問", "/faq/", []),
    ("ABOUT", "店舗情報", "/about/", []),
    ("CONTACT", "お問い合わせ", "/contact/", []),
]
HEADER_NAV = ["CONCEPT", "MENU", "WORKS", "FAQ", "ABOUT"]

# ---------------------------------------------------------------------------
# よくあるご質問（TOP・FAQ・各メニューページで共用）
# 回答は現行サイトの文章をもとに誤字・表記を整えたもの
# ---------------------------------------------------------------------------
FAQ = {
    "kakaku": ("価格はどれくらいですか？", "愛車の状態に合わせて最適なプランをご提案します",
               "サブスクプランは月額32,000円（税込）です。その他の施工には定価を設けていません。"
               "同じ車種でも、塗装の状態や保管環境、お客様が目指す「綺麗」は一台ごとに違うためです。"
               "愛車の状態を確認し、しっかりカウンセリングさせていただいたうえで、明瞭なお見積りをご提案します。"
               "カウンセリング・お見積りは無料です。ご納得いただいてから施工いたします。"),
    "bubun": ("部分施工は可能ですか？", "可能です",
              "これまでにも、エアロを新しく付けた、ホイールを新調したなどのご用命をいただき、部分的に施工した実績があります。"),
    "mado": ("窓の撥水のみの施工は可能ですか？", "可能です",
             "良好な視界の確保は、お客様ご自身の安全の確保にもつながります。ご遠慮なくお申し付けください。"),
    "daisha": ("代車はありますか？", "お預かりで施工するお客様にはお出ししています",
               "愛車をお預かりしている間に観光していただくことも可能です。いつでもお貸しできるよう、代車も常に綺麗を保っています。"
               "乗り合わせでお越しいただき、代車不要とすることも可能です。お気軽にご相談ください。"),
    "basho": ("お店はどこにありますか？", "岡山県和気町にあります。住所は公開しておりません",
              "ReNEW.では高級車をお預かりすることが多く、盗難などのリスクからお客様の愛車を守るため、所在地を公開しておりません。"
              "ご予約が確定したお客様に、詳しい場所をご案内しています。"),
    "kengai": ("県外からの利用は可能ですか？", "可能です。県外からのご用命も多数いただいています",
               "南は鹿児島、北は栃木のお客様からもご用命いただいています。代車が不要な場合は、最寄りの駅や空港まで送迎いたします。お気軽にお申し付けください。"),
    "yoyaku": ("いつ頃から予約・相談したらいいですか？", "早ければ早いほど安心です",
               "納車やお乗り換えの時期など、愛車の状況に合わせて、お引き取りや施工のタイミングをご提案いたします。"),
    "noki": ("納期が大きくずれそうで、問い合わせしにくいです", "まずはお気軽にその旨をお伝えください",
             "昨今の車業界では、納車の予定が定まらないことも少なくありません。ReNEW.はお客様のカーライフに寄り添います。まずはお気軽にご相談ください。"),
    "mente": ("メンテナンスは必要ですか？", "綺麗を維持するには、メンテナンスが必要です",
              "施工後のメンテナンスのタイミングは、当店からご案内しています。"),
    "tasha": ("他社でコーティング施工した車のメンテナンスをお願いできますか？", "まずはお気軽にお申し付けください",
              "他社のコーティングによっては、除去が必要になる場合があります。施工前にカウンセリングを行い、愛車をより良い状態にできるよう施工いたします。"),
    "matte": ("マット塗装のコーティングは可能ですか？", "可能です",
              "当店では、マット塗装・ラッピング・プロテクションフィルムのコーティングが可能です。"
              "マット塗装は研磨による下地作りができないため、液剤による下地処理を行ったうえでコーティングを施工します。"),
}
FAQ_CATEGORIES = [
    ("料金・プラン", ["kakaku", "bubun", "mado"]),
    ("ご来店・お預かり", ["daisha", "basho", "kengai", "yoyaku", "noki"]),
    ("施工・メンテナンス", ["mente", "tasha", "matte"]),
]

# ---------------------------------------------------------------------------
# ご依頼の流れ（TOP・FLOW・MENUで共用）
# ---------------------------------------------------------------------------
FLOW = [
    ("お問い合わせ", "フォーム・LINE・Instagram／XのDMからご連絡ください。ご相談は24時間受付中です。"),
    ("無料カウンセリング・お見積り", "愛車の状態を確認し、なりたい綺麗をお伺いしたうえで、施工内容と明瞭なお見積りをご提案します。"),
    ("ご予約・ご来店", "ご予約確定後に所在地をご案内します。お預かりする愛車を盗難などから守るため、住所は公開していません。"),
    ("お預かり・施工", "お預かり中は代車をご用意しています。代車が不要な場合は、最寄りの駅・空港まで送迎いたします。"),
    ("ご納車", "仕上がりを一緒にご確認いただき、ご自宅でのお手入れ方法をご説明します。"),
    ("定期メンテナンス", "綺麗を維持するためのメンテナンスのタイミングをご案内します。"),
]

# 施工事例（素材が届いたらここに追加する。img は /assets/img/works/ 以下）
WORKS = [
    # {"title": "【 MAKER MODEL 】", "cat": "full", "menu": ["ボディコーティング"], "text": "...", "img": "/assets/img/works/xxx.webp"},
]
WORKS_CATS = {"full": "フル施工", "subscription": "サブスク", "option": "個別メニュー"}

# ---------------------------------------------------------------------------
# アイコン（SNSは simple-icons、その他は Material Icons と同じ形をSVGで）
# ---------------------------------------------------------------------------
ICONS = {
    "chevron": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>',
    "add": '<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z"/></svg>',
    "counsel": '<svg class="i-line" viewBox="0 0 48 48" aria-hidden="true"><path d="M6 10h26v17H17l-7 6v-6H6z"/><path d="M36 17h6v16h-4v5l-6-5H20v-2"/><path d="M12 17h14M12 21h9"/></svg>',
    "skill": '<svg class="i-line" viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6l3.6 10.4L38 20l-10.4 3.6L24 34l-3.6-10.4L10 20l10.4-3.6z"/><path d="M37 32l1.5 4.5L43 38l-4.5 1.5L37 44l-1.5-4.5L31 38l4.5-1.5z"/></svg>',
    "keep": '<svg class="i-line" viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6l15 6v11c0 9.5-6.4 16.4-15 19-8.6-2.6-15-9.5-15-19V12z"/><path d="M17 24l5 5 9-10"/></svg>',
}
for _key, _label, _url in SNS:
    _svg = (ROOT / "icons" / f"{_key}.svg").read_text(encoding="utf-8")
    _path = re.search(r'<path d="([^"]+)"', _svg).group(1)
    ICONS[_key] = f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="{_path}"/></svg>'


# ---------------------------------------------------------------------------
# パーツ
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=True)


def button(label, href, extra=""):
    ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
    return f'<a class="rn-button" href="{esc(href)}"{ext}{extra}>{label}{ICONS["chevron"]}</a>'


def sns_links(cls="rn-sns"):
    items = "".join(
        f'<a href="{url}" target="_blank" rel="noopener" aria-label="{label}" data-track="sns_{key}">{ICONS[key]}</a>'
        for key, label, url in SNS
    )
    return f'<div class="{cls}">{items}</div>'


def faq_items(ids):
    out = []
    for i in ids:
        q, lead, body = FAQ[i]
        out.append(
            f'<details class="rn-faq-item" id="faq-{i}"><summary class="rn-faq-q"><span class="rn-faq-badge" aria-hidden="true">Q</span>'
            f'<span class="rn-faq-text">{esc(q)}</span>{ICONS["add"]}</summary>'
            f'<div class="rn-faq-a"><strong>{esc(lead)}</strong>{esc(body)}</div></details>'
        )
    return '<div class="rn-faq">' + "".join(out) + "</div>"


def faq_all():
    parts = []
    for name, ids in FAQ_CATEGORIES:
        parts.append(f'<section class="faq-cat"><h2 class="faq-cat__title">{esc(name)}</h2>{faq_items(ids)}</section>')
    return "".join(parts)


def faq_schema():
    entities = [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": f"{lead}。{body}"}}
        for q, lead, body in FAQ.values()
    ]
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}


def flow(compact=False):
    steps = []
    for n, (title, text) in enumerate(FLOW, 1):
        steps.append(
            f'<li class="rn-flow-step"><div class="rn-flow-num">STEP{n:02d}</div>'
            f'<div class="rn-flow-card"><h3>{esc(title)}</h3><p>{esc(text)}</p></div></li>'
        )
    cls = "rn-flow-list rn-flow-list--grid" if compact else "rn-flow-list"
    return f'<ol class="{cls}">' + "".join(steps) + "</ol>"


# イメージ写真（AI生成）。assets/img/photos/ の同名ファイルを高解像度版や実写に置き換えればそのまま反映される
PHOTOS = [
    ("00-car-black", "スタジオ照明が映り込む黒い車"),
    ("01-buffing", "クロスで車体を拭き上げる手元"),
    ("02-car-silver", "施工ブースに置かれたシルバーの車"),
    ("03-foam-wash", "泡とミットを使った洗車"),
    ("04-polisher", "ポリッシャーによる磨き"),
    ("05-coating", "コーティング剤を塗布する手元"),
    ("06-headlight", "透明感のあるヘッドライト"),
    ("07-glass-water", "撥水したガラスの水滴"),
    ("08-wheel", "磨き上げたホイール"),
    ("09-interior", "黒いレザーの車内"),
    ("10-booth", "照明を備えた施工ブース"),
    ("11-tools", "ポリッシャーやクロスなどの施工道具"),
]


def photo(index, eager=False):
    name, alt = PHOTOS[index]
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img src="/assets/img/photos/{name}.jpg" alt="{esc(alt)}" width="476" height="265" {load} decoding="async">'


def works(n=None, filter_ui=False):
    items = WORKS[:n] if n else WORKS
    cards = []
    if items:
        for w in items:
            tags = "".join(f"<li>{esc(m)}</li>" for m in w["menu"])
            cards.append(
                f'<li class="work-card" data-cat="{w["cat"]}"><figure class="work-card__img"><img src="{w["img"]}" alt="{esc(w["title"])}の施工後の写真" loading="lazy" width="800" height="600"></figure>'
                f'<div class="work-card__body"><p class="work-card__cat">{WORKS_CATS[w["cat"]]}</p><h3>{esc(w["title"])}</h3>'
                f'<p>{esc(w["text"])}</p><ul class="work-card__menu">{tags}</ul></div></li>'
            )
    else:
        # 素材が届くまでの仮表示。WORKS にデータを入れると自動で事例カードに置き換わる
        tiles = "".join(
            f'<li class="work-card__img generated-photo">{photo(i)}</li>' for i in [5, 7, 8, 9, 11, 3][: n or 6]
        )
        return (
            f'<ul class="works-grid works-grid--pending">{tiles}</ul>'
            '<p class="works-pending">施工事例は準備中です。写真とともに順次ご紹介します（掲載中の写真はイメージです）。<br class="pc">'
            '最新の施工は <a href="https://www.instagram.com/renew.bc/" target="_blank" rel="noopener" data-track="sns_instagram">Instagram（@renew.bc）</a> でご覧いただけます。</p>'
        )
    ui = ""
    if filter_ui:
        btns = '<button type="button" class="chip is-active" data-filter="all">すべて</button>' + "".join(
            f'<button type="button" class="chip" data-filter="{k}">{v}</button>' for k, v in WORKS_CATS.items()
        )
        ui = f'<div class="chips" role="group" aria-label="施工メニューで絞り込む">{btns}</div>'
    return ui + '<ul class="works-grid">' + "".join(cards) + "</ul>"


def sub_slots():
    if SITE["sub_slots"]:
        return f'<p class="slots">{esc(SITE["sub_slots"])}</p>'
    return '<p class="slots">現在満枠のため、キャンセル待ちを受け付けています</p>'


def header(is_home):
    links = "".join(f'<li><a href="{u}">{en}</a></li>' for en, ja, u, _ in NAV if en in HEADER_NAV)
    drawer = []
    for en, ja, u, children in NAV:
        sub = "".join(f'<li><a href="{cu}">{esc(cl)}</a></li>' for cl, cu in children)
        sub = f'<ul class="drawer__sub">{sub}</ul>' if sub else ""
        drawer.append(f'<li><a href="{u}"><span class="en">{en}</span><span class="ja">{ja}</span></a>{sub}</li>')
    return f"""<header class="site-header{' site-header--over' if is_home else ''}" data-header>
  <div class="site-header__inner">
    <a class="site-logo" href="/" aria-label="ReNEW. 車の美容院 トップへ">
      <img class="site-logo__black" src="/assets/img/renew-logo-black.png" alt="ReNEW." width="600" height="150">
      <img class="site-logo__white" src="/assets/img/renew-logo-white.png" alt="" width="600" height="150">
      <span class="site-logo__tag">車の美容院</span>
    </a>
    <nav class="gnav" aria-label="メインメニュー"><ul>{links}</ul></nav>
    <a class="header-cta" href="/contact/">無料カウンセリング</a>
    <button class="burger" type="button" aria-label="メニューを開く" aria-expanded="false" aria-controls="drawer" data-burger><span></span><span></span></button>
  </div>
</header>
<div class="drawer" id="drawer" hidden data-drawer>
  <nav aria-label="サイトメニュー"><ul class="drawer__nav">{''.join(drawer)}</ul></nav>
  <div class="drawer__cta">{button('無料カウンセリング', '/contact/')}{button('LINEで相談する', LINE_URL, ' data-track="line_click"')}</div>
  {sns_links()}
</div>"""


def cta():
    return f"""<section class="cta" aria-labelledby="cta-title">
  <div class="container">
    <h2 class="cta__label" id="cta-title">＼ まずはお気軽にご相談から ／</h2>
    <p class="cta__text">愛車の状態を拝見し、最適なプランとお見積りをご提案します。<br class="pc">ご相談は24時間受付中。カウンセリング・お見積りは無料です。</p>
    <div class="cta__buttons">{button('フォームで相談する', '/contact/')}{button('LINEで相談する', LINE_URL, ' data-track="line_click"')}</div>
    {sns_links()}
  </div>
</section>"""


def footer():
    cols = []
    for en, ja, u, children in NAV:
        if en == "HOME":
            continue
        sub = "".join(f'<li><a href="{cu}">{esc(cl)}</a></li>' for cl, cu in children)
        sub = f"<ul>{sub}</ul>" if sub else ""
        cols.append(f'<li><a href="{u}">{ja}</a>{sub}</li>')
    return f"""<footer class="site-footer">
  <div class="container">
    <nav class="site-footer__nav" aria-label="フッターメニュー"><ul>{''.join(cols)}</ul></nav>
    <a class="site-footer__logo" href="/"><img src="/assets/img/renew-logo-black.png" alt="ReNEW." width="600" height="150" loading="lazy"></a>
    <p class="site-footer__name">SOUKI -創綺- 車の美容院</p>
    <p class="site-footer__addr">岡山県和気町（詳しい所在地はご予約確定後にご案内します）</p>
    {sns_links()}
    <p class="site-footer__links"><a href="/privacy/">プライバシーポリシー</a></p>
    <p class="site-footer__note">サイト内の写真はイメージです（AI生成を含みます）。</p>
    <p class="site-footer__copy"><small>Copyright©ReNEW. All rights reserved.</small></p>
  </div>
</footer>
<div class="sp-bar" data-spbar>
  <a href="/contact/">無料カウンセリング</a>
  <a href="{LINE_URL}" target="_blank" rel="noopener" data-track="line_click">{ICONS['line']}LINEで相談</a>
</div>"""


def breadcrumb(items, path):
    crumbs = [("HOME", "/")] + items
    lis = []
    for i, (name, url) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            lis.append(f'<li aria-current="page">{esc(name)}</li>')
        else:
            lis.append(f'<li><a href="{url}">{esc(name)}</a></li>')
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["url"] + u} for i, (n, u) in enumerate(crumbs)
        ],
    }
    return f'<nav class="breadcrumb" aria-label="パンくずリスト"><ol class="container">{"".join(lis)}</ol></nav>', schema


def business_schema():
    return {
        "@context": "https://schema.org",
        "@type": "AutomotiveBusiness",
        "name": "ReNEW.（SOUKI -創綺- 車の美容院）",
        "alternateName": "リニュー",
        "url": SITE["url"] + "/",
        "logo": SITE["url"] + "/assets/img/renew-logo-black.png",
        "image": SITE["url"] + "/ogp.jpg",
        "description": "岡山県和気町のカーディテイリング専門店。洗車・磨き・コーティングで愛車を新車よりも綺麗に。",
        "founder": {"@type": "Person", "name": "岩藤 大貴"},
        "address": {"@type": "PostalAddress", "addressRegion": "岡山県", "addressLocality": "和気町", "addressCountry": "JP"},
        "areaServed": ["岡山県", "日本"],
        "sameAs": [u for _, _, u in SNS],
    }


def ga_tag():
    gid = SITE["ga4_id"]
    if not gid:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gid}');</script>")


def expand(body):
    """ページ本文中のマクロを展開する"""
    body = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: ICONS[m.group(1)], body)
    body = re.sub(r"\{\{btn:([^|}]+)\|([^}]+)\}\}", lambda m: button(m.group(1), m.group(2)), body)
    body = re.sub(r"<!--@faq ([\w,]+)-->", lambda m: faq_items(m.group(1).split(",")), body)
    body = body.replace("<!--@faq-all-->", faq_all())
    body = body.replace("<!--@flow-->", flow()).replace("<!--@flow-compact-->", flow(compact=True))
    body = re.sub(r"<!--@works( \d+)?( filter)?-->", lambda m: works(int(m.group(1)) if m.group(1) else None, bool(m.group(2))), body)
    body = body.replace("<!--@sub-slots-->", sub_slots())
    body = body.replace("<!--@sns-->", sns_links())
    body = re.sub(r"\{\{photo:(\d+)(:eager)?\}\}", lambda m: photo(int(m.group(1)), bool(m.group(2))), body)
    body = body.replace("{{line_url}}", LINE_URL)
    return body


def render(meta, body, path):
    is_home = path == "/"
    canonical = SITE["url"] + path
    title = meta["title"]
    desc = meta["description"]
    schemas = list(meta.get("schema", []))
    if meta.get("business"):
        schemas.append(business_schema())
    if meta.get("faqSchema"):
        schemas.append(faq_schema())
    crumb_html = ""
    if not is_home and meta.get("breadcrumb"):
        crumb_html, crumb_schema = breadcrumb([tuple(b) for b in meta["breadcrumb"]], path)
        schemas.append(crumb_schema)
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") or PREVIEW else ""
    gsc = f'<meta name="google-site-verification" content="{SITE["gsc_verification"]}">' if SITE["gsc_verification"] else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)
    show_cta = meta.get("cta", True)
    body_cls = " ".join(filter(None, ["is-home" if is_home else "", meta.get("bodyClass", "")]))
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{robots}{gsc}
<meta property="og:type" content="{'website' if is_home else 'article'}">
<meta property="og:site_name" content="ReNEW. 車の美容院">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE['url']}/ogp.jpg">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Renew_souki">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&family=Urbanist:wght@600;700&display=swap">
<link rel="stylesheet" href="/assets/css/style.css?v={BUILD_ID}">
{ld}
{ga_tag()}
</head>
<body class="{body_cls}">
<a class="skip" href="#main">本文へスキップ</a>
{header(is_home)}
{crumb_html}
<main id="main">
{expand(body)}
</main>
{cta() if show_cta else ''}
{footer()}
<script src="/assets/js/main.js?v={BUILD_ID}" defer></script>
</body>
</html>
"""


def with_base(text):
    if not BASE_PATH:
        return text
    return re.sub(r'((?:href|src|action)=")/(?!/)', rf"\1{BASE_PATH}/", text)


META_RE = re.compile(r"\A<!--(\{.*?\})-->\s*", re.S)
BUILD_ID = datetime.datetime.now().strftime("%Y%m%d%H%M")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    sitemap = []
    for src in sorted((ROOT / "pages").rglob("*.html")):
        rel = src.relative_to(ROOT / "pages")
        text = src.read_text(encoding="utf-8")
        m = META_RE.match(text)
        if not m:
            raise SystemExit(f"{rel}: 先頭にメタ情報のコメントがありません")
        meta = json.loads(m.group(1))
        body = text[m.end():]
        if rel.name == "index.html":
            path = "/" + (str(rel.parent) + "/" if str(rel.parent) != "." else "")
        else:
            path = "/" + str(rel)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(with_base(render(meta, body, path)), encoding="utf-8")
        if not meta.get("noindex"):
            sitemap.append(path)
    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE['url']}{p}</loc><lastmod>{today}</lastmod></url>" for p in sitemap)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8",
    )
    if PREVIEW:
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    print(f"built {len(sitemap)} indexable pages -> {OUT}" + (" (preview: noindex)" if PREVIEW else ""))


if __name__ == "__main__":
    build()
