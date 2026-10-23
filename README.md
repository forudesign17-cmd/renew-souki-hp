# ReNEW. ホームページ（静的HTML版）

`renew-souki_renewal_spec.md`（仕様書）と `ReNEW-design-system.zip`（デザインシステム）をもとに制作した、レンタルサーバー向けの静的サイトです。

## フォルダ構成

```
src/
  build.py        ビルドスクリプト（共通設定・FAQ・ご依頼の流れ・施工事例のデータもここ）
  pages/          各ページの本文（ヘッダー・フッター・CTAは build.py が付ける）
  static/         そのままコピーされるファイル（CSS・JS・画像・PHP・.htaccess など）
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
| 施工事例の追加 | `src/build.py` の `WORKS` にデータを追加し、写真を `src/static/assets/img/works/` に置く。TOP・各メニュー・WORKSに自動で反映 |
| FAQの文言 | `src/build.py` の `FAQ` |
| フォームの通知先メール | `src/static/contact/config.php` |
| 写真の差し替え | 各ページの `{{photo:N}}`。生成画像の一覧と配置方法は `IMAGE_GENERATION.md` を参照 |

## 計測（GA4）

`ga4_id` を設定すると以下のイベントが送られます：`line_click`、`sns_*`、`tel_tap`、`form_submit`、`generate_lead`（送信完了ページ）。

## デザインについて

仕様書 3-2・3-3 の色・書体は「案」だったため、後から作られたデザインシステム（モノトーン・Noto Sans JP・角丸なし・黒ボタン）に合わせています。

## 公開前に残っている作業（TODO）

ソース内の `TODO` コメントと対応しています。

- [x] AI生成画像の配置：12カットを個別のJPEGに切り分けて各ページに配置
- [ ] ヒーロー用画像の高解像度化（いまは約480px幅で、全画面表示ではぼやける。`IMAGE_GENERATION.md` 参照）
- [ ] 代表・実際の施工事例・工房設備・Instagramの実写素材への差し替え（現在はAI生成イメージを明記）
- [ ] 施工事例のデータ（`WORKS`）：いまは「準備中」の仮カードを表示中
- [ ] 営業時間・定休日（`/about/`）
- [ ] サブスクの契約条件（最低期間・解約・対象車種）と現在の空き枠
- [ ] 個別メニューの正式なメニュー名・説明（いまは仕様書の例）
- [ ] 返信までの目安「〇営業日以内」（`/contact/thanks/`）
- [ ] プライバシーポリシーの制定日
- [ ] フォームの通知先メールアドレス（`config.php`）、SPF/DKIM の設定
- [ ] ロゴのSVG化（いまは元サイトから取得した600px幅のPNG。ベクターデータをお店から受け取ったら差し替え）
- [ ] OGP画像（`ogp.jpg`）は仮でロゴのみ。写真入りの1200×630に差し替え推奨
- [ ] 送信フォームの動作確認：PHPのあるサーバー上で、通知メール・自動返信が届くか（迷惑メール判定も）確認する
- [ ] スパム対策を強めたい場合は Cloudflare Turnstile を設定（`config.php` とフォームにウィジェットを追加）
- [ ] 公開時：`.htaccess` の301リダイレクト確認、sitemap.xml の送信（仕様書 7・12 のチェックリスト）
