# Instagram タイルの自動更新（設定手順）

TOPの「INSTAGRAM」のタイル（6枚）を、Instagram の最新投稿から**毎日自動で更新**します。
仕組み：GitHub Actions が毎日 3:00（日本時間）に Instagram の公式API から最新の投稿を取得し、サイトを作り直して公開します。

- 設定（トークンの登録）をするまでは、これまでどおり手動で置いた画像（`src/static/assets/img/instagram/`）が表示されます。
- 取得に失敗した日は、前回までの画像のまま表示されます（サイトは壊れません）。
- トークンの有効期限は約60日ですが、毎日の実行のたびに延長されるので、毎日動いていれば切れません。

## あなた（お店のアカウントの持ち主）が行う作業

> Meta 側の画面の名称は変わることがあります。見つからないときは「Instagram API（Instagramログイン）」で検索してください。

### 1. Instagram をプロアカウントにする（まだの場合）
Instagram アプリ → 設定 → アカウントの種類とツール → 「プロアカウントに切り替える」（ビジネスまたはクリエイター）。

### 2. Meta のアプリを作る
1. https://developers.facebook.com/ に、Instagram のアカウントと連携している Facebook アカウントでログインし、開発者として登録する。
2. 「アプリを作成」→ ユースケースで **Instagram** 系（「Instagramの API を使ってメッセージの管理やコンテンツの公開をする」など）を選んで作成する。
3. アプリの管理画面で **「Instagram API（Instagramログインを使用）」の設定**を開く。

### 3. アクセストークンを発行する
1. 同じ画面の「アクセストークンを生成」で、お店の Instagram アカウントを追加し、ログインして許可する。
   （権限は `instagram_business_basic` で足ります）
2. 表示された**トークン（長い文字列）をコピー**する。このトークンは**パスワードと同じ**です。他の人に見せたり、チャットなどに貼ったりしないでください。

### 4. GitHub に登録する
1. GitHub のリポジトリ（forudesign17-cmd/renew-souki-hp）→ Settings → Secrets and variables → Actions → **New repository secret**
2. Name: `IG_ACCESS_TOKEN` / Secret: コピーしたトークン → Add secret

### 5. 動作確認
GitHub のリポジトリ → Actions → 「Deploy preview to GitHub Pages」→ Run workflow を実行。
ログの「Instagramの最新投稿を取得」に `最新の投稿6件を取得しました。` と出て、TOPのタイルが最新の投稿になっていれば完了です。

## うまくいかないとき
| 症状 | 見るところ |
|---|---|
| 「IG_ACCESS_TOKEN が未設定」と出る | 手順4の Secret 名が `IG_ACCESS_TOKEN` と完全に一致しているか |
| 「投稿の取得に失敗しました」 | トークンの期限切れ・アカウントがプロアカウントでない・権限不足。手順3からやり直してトークンを入れ替える |
| 「新しいトークンが発行されました」 | Secret `IG_ACCESS_TOKEN` を、ログに出た新しい値で差し替える（通常は出ません） |
| タイルが6枚にならない | 使える投稿が3の倍数に満たない場合は、3列に収まる枚数（3 or 6）だけ表示します |

## 本番サーバー（renew-souki.jp）について
この自動更新は、**GitHub Pages の確認用サイト**を毎日作り直します。
レンタルサーバーの本番サイトは、`public_html/` をアップロードして公開する方式のため、**自動では更新されません**。
本番も自動にするには、Actions からサーバーへ自動アップロード（FTP/SFTP）する設定が別途必要です（サーバーの接続情報が必要です）。
