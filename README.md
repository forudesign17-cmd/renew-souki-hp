# ReNEW. ホームページ（静的HTML版）

`renew-souki_renewal_spec.md`（仕様書）と `ReNEW-design-system.zip`（デザインシステム）をもとに制作した、レンタルサーバー向けの静的サイトです。

## 確認用サイト（GitHub Pages）

https://forudesign17-cmd.github.io/renew-souki-hp/

`main` に push すると GitHub Actions がビルドして自動更新します。確認用のため全ページ `noindex`（検索エンジンに載せない）です。お問い合わせはLINE・SNSのDMで受け付けるため、メールフォームはありません。

## フォルダ構成

```
src/
  build.py        ビルドスクリプト（共通設定・FAQ・ご依頼の流れ・施工事例のデータもここ）
  pages/          各ページの本文（ヘッダー・フッター・CTAは build.py が付ける）
  static/         そのままコピーされるファイル（CSS・JS・画像・.htaccess など）
  icons/          SNSアイコンのSVG（simple-icons）
public_html/      ビルド結果。この中身をサーバーの公開フォルダへアップロードする
```

## ビルド

Python 3 だけで動きます（追加のインストールは不要）。

```bash
python3 src/build.py
```

テスト環境をサブディレクトリ（例：`https://example.com/test/`）に置く場合は、リンクの先頭を付け替えてビルドします。

```bash
BASE_PATH=/test python3 src/build.py
```

## よく触る場所

| やりたいこと | 場所 |
|---|---|
| サブスクの枠表示（「先着5台限定」／満枠） | `src/build.py` の `SITE["sub_slots"]`。`None` にすると「キャンセル待ち受付中」に切り替わる |
| GA4・Search Console | `src/build.py` の `SITE["ga4_id"]`・`SITE["gsc_verification"]` |
| 施工事例（WORKS）の公開 | 現在は**非公開**（ページ・ナビ・TOP等のリンクをすべて出さない）。`src/build.py` の `WORKS` にデータを入れたあと、`SITE["works_public"]` を `True` にしてビルドすると、WORKSページとすべての導線が一度に現れる |
| 施工事例の追加 | `src/build.py` の `WORKS` にデータを追加し、写真を `src/static/assets/img/works/` に置く。TOP・各メニュー・WORKSに自動で反映 |
| TOPのInstagram（6枚のタイル）の自動更新 | `docs/INSTAGRAM_AUTO_UPDATE.md` の手順でトークンを登録すると、毎日自動で最新の投稿になる（登録するまでは手動の画像のまま） |
| TOPのInstagram（6枚のタイル）を手動で差し替える | 画像を `src/static/assets/img/instagram/` に置き、`src/build.py` の `INSTAGRAM_POSTS`（ファイル名・代替テキスト・投稿URL）を書き換える。URLを指定しなければプロフィールへ |
| FAQの文言 | `src/build.py` の `FAQ` |
| 写真の差し替え | 各ページの `{{photo:N}}`。生成画像の一覧と配置方法は `IMAGE_GENERATION.md` を参照 |

## 計測（GA4）

`ga4_id` を設定すると以下のイベントが送られます：`line_click`、`sns_*`、`tel_tap`。

## デザインについて

仕様書 3-2・3-3 の色・書体は「案」だったため、後から作られたデザインシステム（モノトーン・Noto Sans JP・角丸なし・黒ボタン）に合わせています。

## 公開前に残っている作業（TODO）

ソース内の `TODO` コメントと対応しています。

- [x] AI生成画像の配置：12カットを個別のJPEGに切り分けて各ページに配置
- [x] ヒーロー用画像の高解像度化：TOPは実写（2400px幅）、サブスクは実写（2000px四方）に差し替え済み
- [ ] 代表・実際の施工事例などの実写素材への差し替え（現在はAI生成イメージを明記）
- [ ] 施工事例のデータ（`WORKS`）を貯めて、たまったら `SITE["works_public"] = True` で公開（それまでWORKSは非公開）
- [x] プライバシーポリシーの制定日：公開日に設定する仕組みを用意（公開日に `SITE["privacy_date"]` を入れる。下の「公開日の手順」参照）
- [x] ロゴのSVG化：元の600px幅PNGから自動トレースして作成（`tools/trace_logo.py`）。数倍以上に拡大すると輪郭に小さな乱れが出るので、印刷物などに使う場合は、お店から元のベクターデータ（Illustrator等）を受け取って差し替える
- [x] OGP画像（`ogp.jpg`）：TOPのヒーロー写真＋ロゴ＋キャッチコピーの1200×630を作成済み（`swift tools/make_ogp.swift` で再作成できる）
- [ ] Instagramの自動更新：お客様のアカウントなので、`docs/INSTAGRAM_CLIENT_GUIDE.md`（お客様向け案内）に沿って連携し、`docs/INSTAGRAM_AUTO_UPDATE.md` の手順でトークンを登録する（本番サーバーへの自動反映は別途FTP設定が必要）
- [ ] 公開日：下の「公開日の手順」に沿って実施（`.htaccess` の転送確認・sitemap送信などを含む）

## 公開日の手順（レンタルサーバーへの切り替え）

1. **設定を入れる**（`src/build.py` の `SITE`）
   - `privacy_date`：公開日を `"2026年〇月〇日"` の形で入れる（プライバシーポリシーの制定日になる）
   - `ga4_id`：計測する場合は GA4 の測定ID（`G-XXXXXXXXXX`）
   - `gsc_verification`：現行サイトから引き継ぎ済み（`LQzBxYGap8Ev0xBrfK_HmG-XuSWJJDDmi1ICG3eRCoU`）
2. **本番用にビルド**：`python3 src/build.py`（`BASE_PATH` や `PREVIEW` を付けない。付けると確認用になり、検索に出ない設定になる）
3. **アップロード**：`public_html/` の中身をサーバーの公開フォルダへ。**`.htaccess` も忘れずに**（隠しファイルなので注意）
4. **DNS・SSL**：ドメインをレンタルサーバーへ向け、無料SSLを設定する。**`www.renew-souki.jp` にもDNS（Aレコード or CNAME）とSSLを設定する**（wwwなしへの転送に必要）
5. **点検**：`python3 tools/check_launch.py` を実行して、❌が無いことを確認する（旧URLの転送、https・wwwの統一、サイトマップ、検索設定、404など約30項目）
6. **Search Console**：サイトマップ `https://renew-souki.jp/sitemap.xml` を送信する（確認タグは設置済み）
7. **STUDIO** は、切り替え後1〜2週間ほど様子を見てから公開停止・解約する

> サイトマップの更新日（`lastmod`）は、各ページのファイルを最後にコミットした日になる。本番用のビルドは、履歴のあるこのリポジトリで行うこと。
